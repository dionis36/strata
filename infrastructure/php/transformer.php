<?php
/**
 * Module A: The Refactoring sidecar
 * Performs surgical AST-based transformations on PHP source code.
 */

require __DIR__ . '/vendor/autoload.php';

use PhpParser\Error;
use PhpParser\NodeTraverser;
use PhpParser\ParserFactory;
use PhpParser\NodeVisitor\NameResolver;
use PhpParser\NodeVisitorAbstract;
use PhpParser\Node;
use PhpParser\PrettyPrinter;

class ExtractionVisitor extends NodeVisitorAbstract {
    private $targetClass;
    private $extractedNode = null;

    public function __construct($targetClass) {
        $this->targetClass = $targetClass;
    }

    public function leaveNode(Node $node) {
        if ($node instanceof Node\Stmt\Class_ || $node instanceof Node\Stmt\Interface_ || $node instanceof Node\Stmt\Trait_) {
            if ((string)$node->name === $this->targetClass) {
                $this->extractedNode = $node;
            }
        }
    }

    public function getExtractedNode() {
        return $this->extractedNode;
    }
}

// ── Command Loop ─────────────────────────────────────────────────────────────
// Listens for JSON commands via STDIN
$parser = (new ParserFactory())->create(ParserFactory::PREFER_PHP7);
$printer = new PrettyPrinter\Standard;

while ($line = fgets(STDIN)) {
    $command = json_decode($line, true);
    if (!$command) continue;

    $action = $command['action'] ?? null;
    $filePath = $command['file_path'] ?? null;
    $target = $command['target'] ?? null;

    if ($action === 'EXTRACT_CLASS' && $filePath && $target) {
        try {
            $code = file_get_contents($filePath);
            $stmts = $parser->parse($code);

            // 1. Resolve names to FQNs
            $traverser = new NodeTraverser();
            $traverser->addVisitor(new NameResolver());
            $stmts = $traverser->traverse($stmts);

            // 2. Extract target node
            $extractor = new ExtractionVisitor($target);
            $traverser = new NodeTraverser();
            $traverser->addVisitor($extractor);
            $traverser->traverse($stmts);

            $extracted = $extractor->getExtractedNode();

            if ($extracted) {
                // Wrap in namespace if provided
                $newNamespace = $command['new_namespace'] ?? null;
                if ($newNamespace) {
                    $newStmts = [new Node\Stmt\Namespace_(new Node\Name($newNamespace), [$extracted])];
                } else {
                    $newStmts = [$extracted];
                }

                echo json_encode([
                    'status' => 'success',
                    'code' => $printer->prettyPrintFile($newStmts)
                ]) . "\n";
            } else {
                echo json_encode(['status' => 'error', 'message' => "Class $target not found in $filePath"]) . "\n";
            }

        } catch (Error $e) {
            echo json_encode(['status' => 'error', 'message' => $e->getMessage()]) . "\n";
        }
    } else {
        echo json_encode(['status' => 'error', 'message' => 'Unknown action or missing parameters']) . "\n";
    }
}
