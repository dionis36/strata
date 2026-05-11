<?php

require __DIR__ . '/vendor/autoload.php';

use PhpParser\ParserFactory;
use PhpParser\NodeTraverser;
use PhpParser\NodeVisitor\NameResolver;
use Strata\Parser\MetadataExtractor;

// Initialize Parser
$parser = (new ParserFactory())->createForNewestSupportedVersion();

while ($path = fgets(STDIN)) {
    $path = trim($path);
    if (empty($path)) continue;

    if (!file_exists($path)) {
        echo json_encode(['status' => 'error', 'path' => $path, 'message' => 'File not found']) . "\n";
        continue;
    }

    try {
        $code = file_get_contents($path);
        $stmts = $parser->parse($code);

        $extractor = new MetadataExtractor();
        $traverser = new NodeTraverser();
        $traverser->addVisitor(new NameResolver()); // Resolve FQNs first
        $traverser->addVisitor($extractor);
        $traverser->traverse($stmts);

        echo json_encode([
            'status' => 'success',
            'path' => $path,
            'metadata' => $extractor->metadata
        ]) . "\n";

    } catch (PhpParser\Error $error) {
        echo json_encode([
            'status' => 'error', 
            'path' => $path, 
            'message' => "Parse error: {$error->getMessage()}"
        ]) . "\n";
    }
}
