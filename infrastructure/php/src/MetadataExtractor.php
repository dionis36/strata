<?php

namespace Strata\Parser;

use PhpParser\Node;
use PhpParser\NodeVisitorAbstract;
use PhpParser\Node\Stmt\Class_;
use PhpParser\Node\Stmt\Interface_;
use PhpParser\Node\Stmt\Trait_;
use PhpParser\Node\Stmt\Namespace_;
use PhpParser\Node\Stmt\ClassMethod;
use PhpParser\Node\Stmt\Property;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Expr\StaticCall;
use PhpParser\Node\Expr\New_;

class MetadataExtractor extends NodeVisitorAbstract
{
    public array $metadata = [
        'classes' => [],
        'interfaces' => [],
        'traits' => [],
        'functions' => [], # STANDALONE FUNCTIONS (B requirement)
        'namespaces' => [], # ALL NAMESPACES IN FILE
        'calls' => [],
        'includes' => [],
        'globals' => [],
        'constants' => [],
        'requirements' => [], # For Era/Quality flags
        'complexity' => 1, # Base cyclomatic complexity per file
        'nesting_depth' => 0,
        'max_method_loc' => 0,
        'html_nodes' => 0,
        'echo_nodes' => 0,
        'api_headers' => 0,
        'json_encode' => 0,
        'server_request_uri' => 0
    ];

    private ?string $currentNamespace = null;
    private ?string $currentClass = null;
    private ?string $currentMethod = null;
    private ?string $currentFunction = null;
    
    private int $currentNestingDepth = 0;
    private int $maxNestingDepth = 0;
    private int $maxMethodLoc = 0;

    private function resolveType($type): ?string
    {
        if ($type instanceof Node\NullableType) {
            return '?' . $this->resolveType($type->type);
        }
        if ($type instanceof Node\UnionType) {
            return implode('|', array_map([$this, 'resolveType'], $type->types));
        }
        if ($type instanceof Node\IntersectionType) {
            return implode('&', array_map([$this, 'resolveType'], $type->types));
        }
        if ($type instanceof Node\Identifier || $type instanceof Node\Name) {
            return (string) $type;
        }
        return $type ? (string) $type : null;
    }

    private function resolveClassName($node): ?string
    {
        if ($node instanceof Node\Name && $node->isFullyQualified()) {
            return ltrim((string) $node, '\\');
        }

        $name = (string) $node;
        if ($name === 'self' || $name === 'static') {
            return $this->currentClass;
        }
        if ($name === 'parent') {
            return $this->metadata['classes'][$this->currentClass]['extends'] ?? null;
        }

        # If it's a namespaced name that wasn't FQN, it might have been resolved by NameResolver
        if ($node instanceof Node\Name && $node->hasAttribute('resolvedName')) {
            return ltrim((string) $node->getAttribute('resolvedName'), '\\');
        }

        return ltrim($name, '\\');
    }

    public function enterNode(Node $node)
    {
        // --- Cyclomatic Complexity Heuristic ---
        if ($node instanceof Node\Stmt\If_ || 
            $node instanceof Node\Stmt\For_ || 
            $node instanceof Node\Stmt\Foreach_ || 
            $node instanceof Node\Stmt\While_ || 
            $node instanceof Node\Stmt\Do_ || 
            $node instanceof Node\Stmt\Catch_ || 
            $node instanceof Node\Expr\BinaryOp\BooleanAnd || 
            $node instanceof Node\Expr\BinaryOp\BooleanOr || 
            $node instanceof Node\Expr\Ternary ||
            $node instanceof Node\Stmt\Case_) {
            $this->metadata['complexity']++;
            
            if ($this->currentClass) {
                if (!isset($this->metadata['classes'][$this->currentClass]['wmc'])) {
                    $this->metadata['classes'][$this->currentClass]['wmc'] = 0;
                }
                $this->metadata['classes'][$this->currentClass]['wmc']++;
                
                if ($this->currentMethod) {
                    $methodIndex = count($this->metadata['classes'][$this->currentClass]['methods']) - 1;
                    if ($methodIndex >= 0) {
                        if (!isset($this->metadata['classes'][$this->currentClass]['methods'][$methodIndex]['complexity'])) {
                            $this->metadata['classes'][$this->currentClass]['methods'][$methodIndex]['complexity'] = 1;
                        }
                        $this->metadata['classes'][$this->currentClass]['methods'][$methodIndex]['complexity']++;
                    }
                }
            }
        }

        // --- Nesting Depth ---
        if ($node instanceof Node\Stmt\If_ || 
            $node instanceof Node\Stmt\For_ || 
            $node instanceof Node\Stmt\Foreach_ || 
            $node instanceof Node\Stmt\While_ || 
            $node instanceof Node\Stmt\Do_ || 
            $node instanceof Node\Stmt\Catch_) {
            $this->currentNestingDepth++;
            if ($this->currentNestingDepth > $this->maxNestingDepth) {
                $this->maxNestingDepth = $this->currentNestingDepth;
                $this->metadata['nesting_depth'] = $this->maxNestingDepth;
            }
        }

        // --- Presentation Layer (MVC Deficit) ---
        if ($node instanceof Node\Stmt\InlineHTML) {
            $this->metadata['html_nodes']++;
        }
        if ($node instanceof Node\Stmt\Echo_ || $node instanceof Node\Stmt\Print_) {
            $this->metadata['echo_nodes']++;
        }

        // --- API Surface: REQUEST_URI ---
        if ($node instanceof Node\Expr\ArrayDimFetch && $node->var instanceof Node\Expr\Variable) {
            if ($node->var->name === '_SERVER' && $node->dim instanceof Node\Scalar\String_) {
                if ($node->dim->value === 'REQUEST_URI') {
                    $this->metadata['server_request_uri']++;
                }
            }
        }

        if ($node instanceof Namespace_) {
            $nsName = (string) $node->name;
            $this->currentNamespace = $nsName;
            $this->metadata['namespaces'][] = [
                'name' => $nsName,
                'line' => $node->getLine()
            ];
        }

        if ($node instanceof Class_) {
            $namespacedName = $node->namespacedName ? ltrim((string) $node->namespacedName, '\\') : (string) $node->name;
            $this->currentClass = $namespacedName;
            
            $docComment = $node->getDocComment();
            $docText = $docComment ? $docComment->getText() : null;

            $this->metadata['classes'][$this->currentClass] = [
                'name' => (string) $node->name,
                'fqn' => $this->currentClass,
                'extends' => $node->extends ? (string) $node->extends : null,
                'implements' => array_map(fn($i) => (string) $i, $node->implements),
                'methods' => [],
                'properties' => [],
                'doc_comment' => $docText,
                'wmc' => 0,
                'line' => $node->getLine()
            ];
        }

        if ($node instanceof Property) {
            if ($this->currentClass) {
                foreach ($node->props as $prop) {
                    $this->metadata['classes'][$this->currentClass]['properties'][] = [
                        'name' => (string) $prop->name,
                        'isStatic' => $node->isStatic(),
                        'visibility' => $node->isPublic() ? 'public' : ($node->isProtected() ? 'protected' : 'private')
                    ];
                }
            }
        }

        if ($node instanceof Interface_) {
            $namespacedName = $node->namespacedName ? ltrim((string) $node->namespacedName, '\\') : (string) $node->name;
            $this->metadata['interfaces'][$namespacedName] = [
                'name' => (string) $node->name,
                'extends' => array_map(fn($e) => (string) $e, $node->extends),
                'line' => $node->getLine()
            ];
        }

        if ($node instanceof Trait_) {
            $namespacedName = $node->namespacedName ? ltrim((string) $node->namespacedName, '\\') : (string) $node->name;
            $this->metadata['traits'][$namespacedName] = [
                'name' => (string) $node->name,
                'line' => $node->getLine()
            ];
        }

        if ($node instanceof ClassMethod && $this->currentClass) {
            $methodName = (string)$node->name;
            $this->currentMethod = $methodName;
            
            $isMagic = strpos($methodName, '__') === 0;
            
            $loc = $node->getEndLine() - $node->getStartLine() + 1;
            if ($loc > $this->maxMethodLoc) {
                $this->maxMethodLoc = $loc;
                $this->metadata['max_method_loc'] = $this->maxMethodLoc;
            }

            $this->metadata['classes'][$this->currentClass]['methods'][] = [
                'name' => $methodName,
                'visibility' => $node->isPublic() ? 'public' : ($node->isProtected() ? 'protected' : 'private'),
                'isStatic' => $node->isStatic(),
                'isMagic' => $isMagic,
                'returnType' => $this->resolveType($node->returnType),
                'line' => $node->getLine(),
                'loc' => $loc,
                'complexity' => 1,
                'accessed_properties' => [],
                'globals' => []
            ];

            if ($methodName === '__construct') {
                foreach ($node->params as $param) {
                    if ($param->type) {
                        $paramType = $this->resolveType($param->type);
                        if ($paramType && (strpos($paramType, '\\') !== false || ctype_upper(substr($paramType, 0, 1)))) {
                            $this->metadata['calls'][] = [
                                'type' => 'injection',
                                'class' => $paramType,
                                'line' => $node->getLine(),
                                'source' => $this->currentClass,
                                'sourceMethod' => '__construct'
                            ];
                        }
                    }
                }
            }
        }

        // --- Autoloading & Standalone Functions (Requirement B) ---
        if ($node instanceof Node\Stmt\Function_) {
            $funcName = (string)$node->name;
            $fqn = $this->currentNamespace ? $this->currentNamespace . '\\' . $funcName : $funcName;
            $this->currentFunction = $fqn;
            
            $this->metadata['functions'][$fqn] = [
                'name' => $funcName,
                'fqn' => $fqn,
                'line' => $node->getLine(),
                'returnType' => $this->resolveType($node->returnType),
                'side_effects' => []
            ];

            if ($funcName === '__autoload') {
                $this->metadata['requirements'][] = ['type' => 'LEGACY_AUTOLOAD', 'line' => $node->getLine()];
            }
        }

        // --- Include Tree Extraction (Requirement 3B) ---
        if ($node instanceof Node\Expr\Include_) {
            $includePath = null;
            if ($node->expr instanceof Node\Scalar\String_) {
                $includePath = $node->expr->value;
            }

            $typeStr = 'include';
            switch ($node->type) {
                case Node\Expr\Include_::TYPE_INCLUDE: $typeStr = 'include'; break;
                case Node\Expr\Include_::TYPE_INCLUDE_ONCE: $typeStr = 'include_once'; break;
                case Node\Expr\Include_::TYPE_REQUIRE: $typeStr = 'require'; break;
                case Node\Expr\Include_::TYPE_REQUIRE_ONCE: $typeStr = 'require_once'; break;
            }

            $this->metadata['includes'][] = [
                'type' => $typeStr,
                'path' => $includePath,
                'is_dynamic' => !($node->expr instanceof Node\Scalar\String_),
                'line' => $node->getLine(),
                'source_class' => $this->currentClass,
                'source_method' => $this->currentMethod
            ];
        }

        // --- Global State Mapping (Requirement 3C) ---
        if ($node instanceof Node\Stmt\Global_) {
            foreach ($node->vars as $var) {
                if ($var instanceof Node\Expr\Variable) {
                    $varName = (string)$var->name;
                    $this->metadata['globals'][] = [
                        'name' => $varName,
                        'type' => 'explicit_global',
                        'line' => $node->getLine(),
                        'sourceClass' => $this->currentClass,
                        'sourceMethod' => $this->currentMethod,
                        'sourceFunction' => $this->currentFunction
                    ];
                }
            }
        }

        $superglobals = ['GLOBALS', '_SESSION', '_POST', '_GET', '_COOKIE', '_FILES', '_SERVER', '_REQUEST', '_ENV'];
        
        // Detect Mutations
        if ($node instanceof Node\Expr\Assign) {
            if ($node->var instanceof Node\Expr\Variable && in_array((string)$node->var->name, $superglobals)) {
                $this->metadata['globals'][] = [
                    'name' => (string)$node->var->name,
                    'type' => 'mutation',
                    'line' => $node->getLine(),
                    'sourceClass' => $this->currentClass,
                    'sourceMethod' => $this->currentMethod,
                    'sourceFunction' => $this->currentFunction
                ];
            }
            if ($node->var instanceof Node\Expr\ArrayDimFetch && $node->var->var instanceof Node\Expr\Variable) {
                if (in_array((string)$node->var->var->name, $superglobals)) {
                    // Extract the string key if it is a literal (e.g. $_SESSION['user'])
                    $accessKey = null;
                    if ($node->var->dim instanceof Node\Scalar\String_) {
                        $accessKey = $node->var->dim->value;
                    }
                    $this->metadata['globals'][] = [
                        'name'           => (string)$node->var->var->name,
                        'type'           => 'mutation',
                        'key'            => $accessKey,
                        'line'           => $node->getLine(),
                        'sourceClass'    => $this->currentClass,
                        'sourceMethod'   => $this->currentMethod,
                        'sourceFunction' => $this->currentFunction
                    ];
                }
            }
        }

        // Detect Usage (plain variable: $_SESSION, $_POST, etc.)
        if ($node instanceof Node\Expr\Variable && in_array((string)$node->name, $superglobals)) {
            $this->metadata['globals'][] = [
                'name'           => (string)$node->name,
                'type'           => 'usage',
                'key'            => null,
                'line'           => $node->getLine(),
                'sourceClass'    => $this->currentClass,
                'sourceMethod'   => $this->currentMethod,
                'sourceFunction' => $this->currentFunction
            ];
        }

        // Detect Array Key Access Usage (e.g. $_SESSION['user'], $_POST['email'])
        if ($node instanceof Node\Expr\ArrayDimFetch && $node->var instanceof Node\Expr\Variable) {
            if (in_array((string)$node->var->name, $superglobals)) {
                $accessKey = null;
                if ($node->dim instanceof Node\Scalar\String_) {
                    $accessKey = $node->dim->value;
                }
                $this->metadata['globals'][] = [
                    'name'           => (string)$node->var->name,
                    'type'           => 'key_access',
                    'key'            => $accessKey,
                    'line'           => $node->getLine(),
                    'sourceClass'    => $this->currentClass,
                    'sourceMethod'   => $this->currentMethod,
                    'sourceFunction' => $this->currentFunction
                ];
            }
        }
        
        // --- LCOM Support: Track accessed class properties ---
        if ($node instanceof Node\Expr\PropertyFetch) {
            if ($node->var instanceof Node\Expr\Variable && $node->var->name === 'this') {
                if ($node->name instanceof Node\Identifier && $this->currentClass && $this->currentMethod) {
                    $propName = (string) $node->name;
                    $methodIndex = count($this->metadata['classes'][$this->currentClass]['methods']) - 1;
                    if ($methodIndex >= 0) {
                        if (!in_array($propName, $this->metadata['classes'][$this->currentClass]['methods'][$methodIndex]['accessed_properties'])) {
                            $this->metadata['classes'][$this->currentClass]['methods'][$methodIndex]['accessed_properties'][] = $propName;
                        }
                    }
                }
            }
        }

        // --- Inline HTML/PHP Mixing (Requirement G) ---
        if ($node instanceof Node\Stmt\InlineHTML) {
            $this->metadata['requirements'][] = [
                'type'  => 'INLINE_HTML',
                'line'  => $node->getLine(),
                'bytes' => strlen($node->value),
            ];
        }

        // --- Variable Variables (Requirement 6) ---
        if ($node instanceof Node\Expr\Variable) {
            if ($node->name instanceof Node\Expr) {
                $this->metadata['requirements'][] = [
                    'type' => 'VARIABLE_VARIABLE',
                    'line' => $node->getLine(),
                    'source_class' => $this->currentClass,
                    'source_method' => $this->currentMethod
                ];
            }
        }

        // --- Config Detection & Procedural Calls (Requirement 14) ---
        if ($node instanceof Node\Expr\FuncCall && $node->name instanceof Node\Name) {
            $funcName = (string)$node->name;
            $funcNameLower = strtolower($funcName);
            
            # Auth Patterns (Requirement 13)
            if (in_array($funcNameLower, ['session_set_save_handler', 'session_start'])) {
                $this->metadata['requirements'][] = ['type' => 'CUSTOM_AUTH', 'line' => $node->getLine()];
            }

            if ($funcNameLower === 'mysqli_connect' || $funcNameLower === 'mysql_connect') {
                if (count($node->args) > 0 && $node->args[0]->value instanceof Node\Scalar\String_) {
                    $this->metadata['requirements'][] = ['type' => 'HARDCODED_DB_CREDENTIALS', 'line' => $node->getLine()];
                }
            }

            // mysql_* family (Requirement G: mysql_* detection)
            $mysqlLegacyFuncs = [
                'mysql_query', 'mysql_fetch_array', 'mysql_fetch_assoc', 'mysql_fetch_row',
                'mysql_fetch_object', 'mysql_num_rows', 'mysql_insert_id', 'mysql_affected_rows',
                'mysql_result', 'mysql_select_db', 'mysql_free_result', 'mysql_real_escape_string',
                'mysql_error', 'mysql_errno', 'mysql_close', 'mysql_connect', 'mysql_pconnect',
            ];
            if (in_array($funcNameLower, $mysqlLegacyFuncs)) {
                $this->metadata['requirements'][] = [
                    'type'     => 'MYSQL_LEGACY',
                    'function' => $funcName,
                    'line'     => $node->getLine(),
                ];
            }

            // register_globals assumption (Requirement G)
            if (in_array($funcNameLower, ['extract', 'import_request_variables'])) {
                $this->metadata['requirements'][] = [
                    'type' => 'REGISTER_GLOBALS_ASSUMPTION',
                    'function' => $funcName,
                    'line' => $node->getLine(),
                ];
            }

            // --- API Surface: JSON & Headers ---
            if ($funcNameLower === 'json_encode') {
                $this->metadata['json_encode']++;
            }
            if ($funcNameLower === 'header') {
                if (isset($node->args[0]) && $node->args[0]->value instanceof Node\Scalar\String_) {
                    $headerVal = strtolower($node->args[0]->value->value);
                    if (strpos($headerVal, 'application/json') !== false) {
                        $this->metadata['api_headers']++;
                    }
                }
            }

            // include-based routing (Requirement G)
            if (in_array($funcNameLower, ['include', 'require', 'include_once', 'require_once', 'exec', 'system', 'shell_exec', 'passthru'])) {
                $this->metadata['requirements'][] = [
                    'type' => in_array($funcNameLower, ['include', 'require', 'include_once', 'require_once']) ? 'INCLUDE_ROUTING' : 'DANGER',
                    'sink' => $funcNameLower,
                    'line' => $node->getLine(),
                ];
            }

            if ($funcNameLower === 'define' && count($node->args) >= 2) {
                $constName = null;
                if ($node->args[0]->value instanceof Node\Scalar\String_) {
                    $constName = $node->args[0]->value->value;
                }
                $this->metadata['constants'][] = [
                    'name' => $constName,
                    'line' => $node->getLine(),
                    'source_class' => $this->currentClass,
                    'source_method' => $this->currentMethod
                ];
            }

            # Register as a general call for the Linker
            $this->metadata['calls'][] = [
                'type' => 'function_call',
                'method' => $funcName, # We use 'method' key for compatibility with the Linker
                'line' => $node->getLine(),
                'source' => $this->currentClass,
                'sourceMethod' => $this->currentMethod,
                'sourceFunction' => $this->currentFunction
            ];
        }

        if ($node instanceof Node\Expr\Eval_) {
            $this->metadata['requirements'][] = [
                'type' => 'DANGER',
                'sink' => 'eval',
                'line' => $node->getLine()
            ];
        }

        // --- Raw SQL Inference (Requirement 11) ---
        if ($node instanceof Node\Scalar\String_) {
            $val = strtolower(trim($node->value));
            if (strpos($val, 'select ') === 0 || strpos($val, 'insert into ') === 0 || 
                strpos($val, 'update ') === 0 || strpos($val, 'delete from ') === 0 ||
                strpos($val, 'call ') === 0 || strpos($val, 'exec ') === 0) {
                
                $type = 'RAW_SQL';
                if (strpos($val, 'call ') === 0 || strpos($val, 'exec ') === 0) {
                    $type = 'STORED_PROCEDURE';
                }
                
                $this->metadata['requirements'][] = [
                    'type' => $type, 
                    'line' => $node->getLine(), 
                    'snippet' => substr($val, 0, 50),
                    'full_query' => $val
                ];
            }
        }

        // --- Call Extraction ---
        if ($node instanceof MethodCall && $node->name instanceof Node\Identifier) {
            $methodName = strtolower((string) $node->name);
            if (in_array($methodName, ['begintransaction', 'commit', 'rollback'])) {
                $this->metadata['requirements'][] = [
                    'type' => 'DB_TRANSACTION',
                    'line' => $node->getLine()
                ];
            }
            
            $this->metadata['calls'][] = [
                'type' => 'method_call',
                'method' => (string) $node->name,
                'line' => $node->getLine(),
                'source' => $this->currentClass,
                'sourceMethod' => $this->currentMethod
            ];
        }

        if ($node instanceof StaticCall && $node->class instanceof Node\Name && $node->name instanceof Node\Identifier) {
            $class = $this->resolveClassName($node->class);
            if ($class) {
                # Custom Framework Detection: jf::import
                if (strtolower($class) === 'jf' && strtolower((string)$node->name) === 'import' && count($node->args) > 0) {
                    if ($node->args[0]->value instanceof Node\Scalar\String_) {
                        $this->metadata['includes'][] = [
                            'type' => 'jf_import',
                            'path' => $node->args[0]->value->value,
                            'line' => $node->getLine()
                        ];
                    }
                }

                $this->metadata['calls'][] = [
                    'type' => 'static_call',
                    'class' => $class,
                    'method' => (string) $node->name,
                    'line' => $node->getLine(),
                    'source' => $this->currentClass,
                    'sourceMethod' => $this->currentMethod,
                    'sourceFunction' => $this->currentFunction
                ];
            }
        }

        if ($node instanceof New_ && $node->class instanceof Node\Name) {
            $class = $this->resolveClassName($node->class);
            if ($class) {
                if (strtolower($class) === 'pdo' && count($node->args) > 0) {
                    if ($node->args[0]->value instanceof Node\Scalar\String_) {
                        $this->metadata['requirements'][] = ['type' => 'HARDCODED_DB_CREDENTIALS', 'line' => $node->getLine()];
                    }
                }
                
                $this->metadata['calls'][] = [
                    'type' => 'instantiation',
                    'class' => $class,
                    'line' => $node->getLine(),
                    'source' => $this->currentClass,
                    'sourceMethod' => $this->currentMethod
                ];
            }
        }

        // --- Side-Effect Detection ---
        $this->detectSideEffects($node);

        return null;
    }

    private function detectSideEffects(Node $node)
    {
        // eval() is a PHP language construct, NOT a FuncCall — handle it explicitly
        if ($node instanceof Node\Expr\Eval_) {
            $this->recordSideEffect('DANGER', $node->getLine());
            return;
        }

        $name = null;
        if ($node instanceof MethodCall) {
            if ($node->name instanceof Node\Identifier) {
                $name = (string) $node->name;
            }
        } elseif ($node instanceof StaticCall) {
            if ($node->name instanceof Node\Identifier || $node->name instanceof Node\Name) {
                $name = (string) $node->name;
            }
        } elseif ($node instanceof Node\Expr\FuncCall) {
            if ($node->name instanceof Node\Name) {
                $name = (string) $node->name;
            }
        }

        if (!$name) return;

        // DB Sinks
        $dbSinks = ['query', 'execute', 'exec', 'persist', 'flush', 'save', 'insert', 'update', 'delete', 'mysql_query', 'mysqli_query', 'pdo_query'];
        // IO Sinks
        $ioSinks = ['file_put_contents', 'fwrite', 'fputs', 'mkdir', 'unlink', 'copy', 'rename', 'chmod', 'chown'];
        // Network Sinks
        $netSinks = ['curl_exec', 'file_get_contents', 'fopen', 'socket_write'];
        // Dangerous Sinks (Requirement 6)
        $dangerSinks = ['eval', 'extract', 'exec', 'passthru', 'system', 'shell_exec'];
        // Hosting/Runtime Sinks (Requirement 15)
        $hostingSinks = ['ini_set', 'set_time_limit', 'header', 'move_uploaded_file'];
        // Template Sinks (Requirement 12)
        $templateSinks = ['render', 'display', 'view', 'fetch'];

        $type = null;
        $lname = strtolower($name);
        if (in_array($lname, $dbSinks)) $type = 'DB';
        elseif (in_array($lname, $ioSinks)) $type = 'IO';
        elseif (in_array($lname, $netSinks)) $type = 'NET';
        elseif (in_array($lname, $dangerSinks)) $type = 'DANGER';
        elseif (in_array($lname, $hostingSinks)) $type = 'HOSTING';
        elseif (in_array($lname, $templateSinks)) $type = 'TEMPLATE';
        elseif (in_array($lname, ['md5', 'sha1'])) $type = 'LEGACY_HASH'; # Requirement 13
        elseif (in_array($lname, ['session_start', 'session_regenerate_id'])) $type = 'AUTH';

        if ($type) {
            if ($this->currentClass && $this->currentMethod) {
                $methodIndex = count($this->metadata['classes'][$this->currentClass]['methods']) - 1;
                if ($methodIndex >= 0) {
                    $this->metadata['classes'][$this->currentClass]['methods'][$methodIndex]['side_effects'][] = $type;
                }
            } elseif ($this->currentFunction) {
                $this->metadata['functions'][$this->currentFunction]['side_effects'][] = $type;
            } else {
                // Procedural side effect (Requirement 1, 3B, 3C)
                $this->metadata['file_side_effects'][] = [
                    'type' => $type,
                    'line' => $node->getLine()
                ];
            }
        }
    }

    private function recordSideEffect(string $type, int $line)
    {
        if ($this->currentClass && $this->currentMethod) {
            $methodIndex = count($this->metadata['classes'][$this->currentClass]['methods']) - 1;
            if ($methodIndex >= 0) {
                $this->metadata['classes'][$this->currentClass]['methods'][$methodIndex]['side_effects'][] = $type;
            }
        } elseif ($this->currentFunction) {
            $this->metadata['functions'][$this->currentFunction]['side_effects'][] = $type;
        } else {
            $this->metadata['file_side_effects'][] = [
                'type' => $type,
                'line' => $line
            ];
        }
    }

    public function leaveNode(Node $node)
    {
        if ($node instanceof Node\Stmt\If_ || 
            $node instanceof Node\Stmt\For_ || 
            $node instanceof Node\Stmt\Foreach_ || 
            $node instanceof Node\Stmt\While_ || 
            $node instanceof Node\Stmt\Do_ || 
            $node instanceof Node\Stmt\Catch_) {
            $this->currentNestingDepth--;
        }

        if ($node instanceof Namespace_) {
            $this->currentNamespace = null;
        }
        if ($node instanceof Class_) {
            $this->currentClass = null;
        }
        if ($node instanceof ClassMethod) {
            $this->currentMethod = null;
        }
        if ($node instanceof Node\Stmt\Function_) {
            $this->currentFunction = null;
        }
        return null;
    }
}
