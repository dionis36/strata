<?php

require __DIR__ . '/vendor/autoload.php';

use PhpParser\ParserFactory;
use PhpParser\NodeTraverser;
use PhpParser\NodeVisitor\NameResolver;
use Strata\Parser\MetadataExtractor;

// Initialize Parser


// Initialize Parser with Legacy Support
// PHP-Parser v5.x uses a new factory pattern. 
// We use the newest supported version to ensure maximum compatibility with both 
// modern and legacy (PHP 5.x/7.x) syntax.
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
        $loc = substr_count($code, "\n") + 1;
        $stmts = $parser->parse($code);

        $extractor = new MetadataExtractor();
        $traverser = new NodeTraverser();
        $traverser->addVisitor(new NameResolver()); // Resolve FQNs first
        $traverser->addVisitor($extractor);
        $traverser->traverse($stmts);

        $metadata = $extractor->metadata;
        $metadata['loc'] = $loc;

        echo json_encode([
            'status' => 'success',
            'path' => $path,
            'metadata' => $metadata
        ]) . "\n";

    } catch (PhpParser\Error $error) {
        echo json_encode([
            'status' => 'error', 
            'path' => $path, 
            'message' => "Parse error: {$error->getMessage()}"
        ]) . "\n";
    }
}
