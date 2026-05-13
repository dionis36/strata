<?php

namespace Strata\Parser;

use PhpParser\Node;
use PhpParser\NodeVisitorAbstract;
use PhpParser\Node\Stmt\Class_;
use PhpParser\Node\Stmt\Interface_;
use PhpParser\Node\Stmt\Trait_;
use PhpParser\Node\Stmt\Namespace_;
use PhpParser\Node\Stmt\ClassMethod;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Expr\StaticCall;
use PhpParser\Node\Expr\New_;

class MetadataExtractor extends NodeVisitorAbstract
{
    public array $metadata = [
        'classes' => [],
        'interfaces' => [],
        'traits' => [],
        'calls' => [],
        'includes' => [],
        'globals' => [],
        'constants' => [],
        'requirements' => [] # For Era/Quality flags
    ];

    private ?string $currentNamespace = null;
    private ?string $currentClass = null;
    private ?string $currentMethod = null;

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

    private function resolveClassName(string $name): ?string
    {
        if ($name === 'self' || $name === 'static') {
            return $this->currentClass;
        }
        if ($name === 'parent') {
            return $this->metadata['classes'][$this->currentClass]['extends'] ?? null;
        }
        return $name;
    }

    public function enterNode(Node $node)
    {
        if ($node instanceof Namespace_) {
            $this->currentNamespace = (string) $node->name;
        }

        if ($node instanceof Class_) {
            $namespacedName = $node->namespacedName ? (string) $node->namespacedName : (string) $node->name;
            $this->currentClass = $namespacedName;
            $this->metadata['classes'][$this->currentClass] = [
                'name' => (string) $node->name,
                'fqn' => $this->currentClass,
                'extends' => $node->extends ? (string) $node->extends : null,
                'implements' => array_map(fn($i) => (string) $i, $node->implements),
                'methods' => [],
                'line' => $node->getLine()
            ];
        }

        if ($node instanceof Interface_) {
            $namespacedName = $node->namespacedName ? (string) $node->namespacedName : (string) $node->name;
            $this->metadata['interfaces'][$namespacedName] = [
                'name' => (string) $node->name,
                'extends' => array_map(fn($e) => (string) $e, $node->extends),
                'line' => $node->getLine()
            ];
        }

        if ($node instanceof Trait_) {
            $namespacedName = $node->namespacedName ? (string) $node->namespacedName : (string) $node->name;
            $this->metadata['traits'][$namespacedName] = [
                'name' => (string) $node->name,
                'line' => $node->getLine()
            ];
        }

        if ($node instanceof ClassMethod && $this->currentClass) {
            $methodName = (string)$node->name;
            $this->currentMethod = $methodName;
            
            $isMagic = strpos($methodName, '__') === 0;

            $this->metadata['classes'][$this->currentClass]['methods'][] = [
                'name' => $methodName,
                'visibility' => $node->isPublic() ? 'public' : ($node->isProtected() ? 'protected' : 'private'),
                'isStatic' => $node->isStatic(),
                'isMagic' => $isMagic,
                'returnType' => $this->resolveType($node->returnType),
                'line' => $node->getLine(),
                'globals' => []
            ];
        }

        // --- Autoloading (Requirement 10) ---
        if ($node instanceof Node\Stmt\Function_ && (string)$node->name === '__autoload') {
            $this->metadata['requirements'][] = ['type' => 'LEGACY_AUTOLOAD', 'line' => $node->getLine()];
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
                        'line' => $node->getLine()
                    ];
                }
            }
        }

        $superglobals = ['GLOBALS', '_SESSION', '_POST', '_GET', '_COOKIE', '_SERVER', '_REQUEST', '_ENV'];
        
        // Detect Mutations
        if ($node instanceof Node\Expr\Assign) {
            if ($node->var instanceof Node\Expr\Variable && in_array((string)$node->var->name, $superglobals)) {
                $this->metadata['globals'][] = [
                    'name' => (string)$node->var->name,
                    'type' => 'mutation',
                    'line' => $node->getLine()
                ];
            }
            if ($node->var instanceof Node\Expr\ArrayDimFetch && $node->var->var instanceof Node\Expr\Variable) {
                if (in_array((string)$node->var->var->name, $superglobals)) {
                    $this->metadata['globals'][] = [
                        'name' => (string)$node->var->var->name,
                        'type' => 'mutation',
                        'line' => $node->getLine()
                    ];
                }
            }
        }

        // Detect Usage
        if ($node instanceof Node\Expr\Variable && in_array((string)$node->name, $superglobals)) {
            $this->metadata['globals'][] = [
                'name' => (string)$node->name,
                'type' => 'usage',
                'line' => $node->getLine()
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

        // --- Config Detection (Requirement 14) ---
        if ($node instanceof Node\Expr\FuncCall && $node->name instanceof Node\Name) {
            $funcName = strtolower((string)$node->name);
            
            # Auth Patterns (Requirement 13)
            if (in_array($funcName, ['session_set_save_handler', 'session_start'])) {
                $this->metadata['requirements'][] = ['type' => 'CUSTOM_AUTH', 'line' => $node->getLine()];
            }

            if ($funcName === 'mysqli_connect' || $funcName === 'mysql_connect') {
                if (count($node->args) > 0 && $node->args[0]->value instanceof Node\Scalar\String_) {
                    $this->metadata['requirements'][] = ['type' => 'HARDCODED_DB_CREDENTIALS', 'line' => $node->getLine()];
                }
            }

            if ($funcName === 'define' && count($node->args) >= 2) {
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
            $class = $this->resolveClassName((string) $node->class);
            if ($class) {
                $this->metadata['calls'][] = [
                    'type' => 'static_call',
                    'class' => $class,
                    'method' => (string) $node->name,
                    'line' => $node->getLine(),
                    'source' => $this->currentClass,
                    'sourceMethod' => $this->currentMethod
                ];
            }
        }

        if ($node instanceof New_ && $node->class instanceof Node\Name) {
            $class = $this->resolveClassName((string) $node->class);
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
        $name = null;
        if ($node instanceof MethodCall) {
            $name = (string) $node->name;
        } elseif ($node instanceof StaticCall) {
            $name = (string) $node->name;
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
            } else {
                // Procedural side effect (Requirement 1, 3B, 3C)
                $this->metadata['file_side_effects'][] = [
                    'type' => $type,
                    'line' => $node->getLine()
                ];
            }
        }
    }

    public function leaveNode(Node $node)
    {
        if ($node instanceof Namespace_) {
            $this->currentNamespace = null;
        }
        if ($node instanceof Class_) {
            $this->currentClass = null;
        }
        if ($node instanceof ClassMethod) {
            $this->currentMethod = null;
        }
        return null;
    }
}
