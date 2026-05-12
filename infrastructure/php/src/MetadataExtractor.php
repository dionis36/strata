<?php

namespace Strata\Parser;

use PhpParser\Node;
use PhpParser\Node\Stmt\Class_;
use PhpParser\Node\Stmt\Interface_;
use PhpParser\Node\Stmt\Trait_;
use PhpParser\Node\Stmt\Namespace_;
use PhpParser\Node\Stmt\ClassMethod;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Expr\StaticCall;
use PhpParser\Node\Expr\New_;
use PhpParser\NodeVisitorAbstract;

class MetadataExtractor extends NodeVisitorAbstract
{
    public array $metadata = [
        'classes' => [],
        'interfaces' => [],
        'traits' => [],
        'calls' => []
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
            $this->currentMethod = (string) $node->name;
            $this->metadata['classes'][$this->currentClass]['methods'][] = [
                'name' => (string) $node->name,

                'visibility' => $node->isPublic() ? 'public' : ($node->isProtected() ? 'protected' : 'private'),
                'isStatic' => $node->isStatic(),
                'returnType' => $this->resolveType($node->returnType),
                'line' => $node->getLine()
            ];
        }

        // --- Call Extraction ---

        if ($node instanceof MethodCall) {
            $this->metadata['calls'][] = [
                'type' => 'method_call',
                'method' => (string) $node->name,
                'line' => $node->getLine(),
                'source' => $this->currentClass,
                'sourceMethod' => $this->currentMethod
            ];
        }

        if ($node instanceof StaticCall) {
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

        if ($node instanceof New_) {
            $class = $this->resolveClassName((string) $node->class);
            if ($class) {
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
            $name = (string) $node->name;
        }

        if (!$name) return;

        // DB Sinks
        $dbSinks = ['query', 'execute', 'exec', 'persist', 'flush', 'save', 'insert', 'update', 'delete', 'mysql_query', 'mysqli_query', 'pdo_query'];
        // IO Sinks
        $ioSinks = ['file_put_contents', 'fwrite', 'fputs', 'mkdir', 'unlink', 'copy', 'rename'];
        // Network Sinks
        $netSinks = ['curl_exec', 'file_get_contents', 'fopen', 'socket_write'];

        $type = null;
        $lname = strtolower($name);
        if (in_array($lname, $dbSinks)) $type = 'DB';
        elseif (in_array($lname, $ioSinks)) $type = 'IO';
        elseif (in_array($lname, $netSinks)) $type = 'NET';

        if ($type && $this->currentClass && $this->currentMethod) {
            // Find the current method in the metadata and tag it
            $methodIndex = count($this->metadata['classes'][$this->currentClass]['methods']) - 1;
            if ($methodIndex >= 0) {
                $this->metadata['classes'][$this->currentClass]['methods'][$methodIndex]['side_effects'][] = $type;
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
