Building a legacy PHP modernization decision-support tool is a strong idea because most real-world PHP systems were not built with modern architecture assumptions. Your advantage comes from understanding how *legacy PHP actually evolved in the wild*, not just how PHP “should” be written.

You need to think like someone maintaining systems from:

* PHP 4
* early PHP 5
* shared hosting environments
* cPanel deployments
* DreamHost/HostGator-era applications
* pre-framework CMS/custom ERP systems
* copied-and-pasted codebases
* mixed HTML/PHP procedural apps

---

# 1. Understand the Eras of Legacy PHP

This is critical because architecture patterns strongly correlate with PHP versions.

## Era A — PHP 3 / PHP 4 (1998–2004)

Typical characteristics:

* No namespaces
* Mostly procedural
* Includes everywhere
* Global variables
* `mysql_*` functions
* Inline HTML + PHP mixed
* Business logic inside templates
* Shared hosting assumptions
* No Composer
* No autoloading
* No dependency injection

Common files:

```php
config.php
db.php
functions.php
header.php
footer.php
menu.php
index.php
login.php
```

Patterns:

```php
include("config.php");

$conn = mysql_connect(...);

$result = mysql_query("SELECT * FROM users");
```

---

## Era B — PHP 5 Early (2004–2010)

Transitional era.

You start seeing:

* primitive OOP
* homemade MVC
* PEAR
* Zend Framework 1
* CodeIgniter
* custom autoloaders
* singleton abuse

Still common:

* globals
* static helper classes
* registry containers
* fat controllers

Example:

```php
class Database {
    static function getInstance() {
    }
}
```

---

## Era C — PHP 5.3+ (Namespaces introduced)

Namespaces appear:

```php
namespace App\Controllers;
```

BUT most legacy systems still avoided them for years.

Important:
A huge percentage of legacy PHP apps STILL use global namespace even today.

---

## Era D — Modern PHP (2015+)

Modernization targets usually look like:

* PSR-4
* Composer
* Laravel/Symfony
* typed properties
* dependency injection
* service containers
* REST APIs
* domain-driven design

Your tool bridges old → modern.

---

# 2. The REAL Structure of Legacy PHP Systems

Your analyzer must understand reality, not ideal architecture.

---

# 3. Common Legacy PHP Architectural Patterns

## A. Page Controller Architecture

Most common.

Each PHP file = endpoint.

Example:

```text
/public
    users.php
    login.php
    orders.php
```

Inside:

```php
if ($_POST['save']) {
    saveUser();
}

showPage();
```

Your tool should detect:

* request handling
* form submission flows
* redirect chains
* page responsibilities

---

## B. Include Trees

Legacy systems rely heavily on:

```php
include
include_once
require
require_once
```

Important:
This creates an *implicit dependency graph*.

Your analyzer should build:

* include graph
* bootstrap chain
* circular include detection
* dead include detection

Example:

```text
index.php
 └── config.php
      └── db.php
           └── functions.php
```

This is one of the MOST important modernization insights.

---

## C. Global State Architecture

Legacy PHP systems rely on:

* `$GLOBALS`
* global variables
* superglobals
* session globals

Example:

```php
global $db;
global $user;
```

OR:

```php
$GLOBALS['config']
```

Your tool should map:

* global variable origins
* mutation points
* cross-file global usage

This is crucial for migration risk analysis.

---

# 4. Namespace Reality

## Most Legacy Systems Use Global Namespace

Example:

```php
class User {
}
```

NOT:

```php
namespace App\Models;
```

Meaning:

* class collisions possible
* function collisions common
* helper duplication everywhere

Your tool should:

* detect namespace usage
* detect global namespace pollution
* recommend PSR-4 migration map

---

# 5. Legacy File Organization Patterns

## Common Structures

### Flat structure

```text
/
    index.php
    login.php
    users.php
    db.php
```

### Semi-organized

```text
/admin
/includes
/classes
/lib
/templates
```

### Fake MVC

```text
/controllers
/models
/views
```

But still procedural internally.

---

# 6. Important Legacy PHP Features To Detect

## Deprecated Database APIs

### mysql_* API

```php
mysql_query()
mysql_connect()
```

High modernization priority.

---

## Dangerous Patterns

### eval

```php
eval($code);
```

### Variable variables

```php
$$name
```

### Dynamic includes

```php
include($_GET['page']);
```

### extract()

```php
extract($_POST);
```

### register_globals assumptions

Very old systems assume:

```php
$username
```

instead of:

```php
$_POST['username']
```

---

# 7. Static Analysis Areas You Need

Your tool should perform layered analysis.

---

# Layer 1 — File System Analysis

Detect:

* file types
* entry points
* includes
* assets
* uploads
* vendor libs
* framework signatures

Artifacts:

* architecture map
* folder classification
* dependency graph

---

# Layer 2 — PHP AST Analysis

Use AST parsing.

Important libraries:

* [nikic/PHP-Parser](https://github.com/nikic/PHP-Parser?utm_source=chatgpt.com)
* [PHPStan](https://phpstan.org?utm_source=chatgpt.com)
* [Psalm](https://psalm.dev?utm_source=chatgpt.com)

You need AST, not regex.

Detect:

* classes
* functions
* inheritance
* interfaces
* traits
* namespaces
* globals
* database calls
* HTTP flows

---

# Layer 3 — Semantic Architecture Analysis

This is where your tool becomes valuable.

Infer:

* bounded contexts
* modules
* business domains
* coupling
* transaction flows
* auth flows
* reporting modules

This is hard and becomes your differentiator.

---

# 8. Build a "Modernization Score"

Very useful.

Example dimensions:

| Area                      | Score |
| ------------------------- | ----- |
| PHP Version Compatibility | 20    |
| Namespace Adoption        | 10    |
| DB Layer Quality          | 15    |
| Security Risk             | 20    |
| Framework Alignment       | 10    |
| Testability               | 10    |
| Coupling                  | 15    |

Then output:

* low-risk modernization
* medium-risk
* rewrite recommended

---

# 9. Detect Framework Signatures

Very important.

You should fingerprint:

| Framework   | Signature      |
| ----------- | -------------- |
| WordPress   | wp-config.php  |
| Joomla      | defines.php    |
| Drupal      | sites/default  |
| CodeIgniter | system/core    |
| Zend 1      | Zend/Loader    |
| CakePHP     | app/Controller |
| Laravel     | artisan        |

Legacy apps often contain partial frameworks.

---

# 10. Legacy Autoloading Patterns

Before Composer:

## __autoload

```php
function __autoload($class)
```

## SPL autoload

```php
spl_autoload_register()
```

## Custom naming conventions

```php
User_Model
Admin_Controller
```

Your tool should infer:

* pseudo namespaces
* naming conventions
* migration mapping

---

# 11. Database Analysis

Critical.

Detect:

* raw SQL
* query builders
* ORM usage
* stored procedures
* duplicated queries
* hardcoded credentials
* transaction handling

Also:

* identify table ownership per module
* infer ERD
* infer domain relationships

Huge value.

---

# 12. Template Systems

Legacy PHP templates are chaotic.

Detect:

## Inline templates

```php
<?php foreach(...) { ?>
```

## Smarty

```smarty
{foreach}
```

## Twig

```twig
{{ user.name }}
```

## Blade

```blade
@foreach
```

Important for modernization recommendations.

---

# 13. Authentication Patterns

Legacy systems often use:

* MD5 passwords
* SHA1
* homemade sessions
* role arrays
* ACL tables

Detect:

* auth entry points
* middleware absence
* privilege escalation risks

---

# 14. Configuration Detection

Legacy systems store config everywhere.

Common:

```php
config.php
settings.php
constants.php
define(...)
```

Detect:

* environment handling
* hardcoded secrets
* deployment assumptions

---

# 15. Shared Hosting Assumptions

VERY important for legacy systems.

Legacy apps assume:

* Apache mod_php
* writable directories
* no CLI
* no queues
* cron-based jobs
* FTP deployments

Your modernization engine should detect deployment assumptions.

---

# 16. Modernization Recommendation Engine

This becomes your “decision support.”

Example outputs:

## Option A — Incremental Modernization

Recommended if:

* coupling manageable
* PHP 7 compatible
* modular enough

Steps:

1. Add Composer
2. Introduce namespaces
3. Wrap DB layer
4. Add routing
5. Extract services

---

## Option B — Strangler Fig Migration

Recommended if:

* huge procedural monolith
* dangerous coupling

Suggest:

* reverse proxy
* route-by-route replacement
* API facade

---

## Option C — Full Rewrite

Recommended if:

* PHP 4
* no modularity
* security disasters
* impossible coupling

---

# 17. Forward Compatibility Strategy

This matters a LOT.

Your tool should NOT hardcode current PHP assumptions.

Design around:

* AST abstraction
* language-version adapters
* rule engines
* plugin analyzers

Example:

```text
Core Engine
 ├── PHP 5 Adapter
 ├── PHP 7 Adapter
 ├── PHP 8 Adapter
```

---

# 18. Key Technical Capabilities You Need

## Dependency Graph Engine

Absolutely essential.

Build:

* file graph
* class graph
* include graph
* DB graph
* request flow graph

Graph databases help.

Consider:

* [Neo4j](https://neo4j.com?utm_source=chatgpt.com)

---

# 19. Valuable Output Artifacts

Your tool should generate:

## Architecture Documents

* system context
* module map
* dependency diagrams
* data flow diagrams

## Engineering Reports

* tech debt report
* security report
* modernization feasibility

## Migration Plans

* estimated complexity
* phased migration roadmap
* risk analysis

## AI-Friendly Artifacts

Generate:

* JSON knowledge graph
* AST metadata
* embeddings-ready chunks

This enables future AI copilots.

---

# 20. Extremely Important Legacy PHP Edge Cases

Your tool MUST handle:

## Mixed PHP/HTML

```php
<html>
<?php
```

## Output buffering

```php
ob_start();
```

## Magic methods

```php
__get
__call
```

## Dynamic method calls

```php
$obj->$method()
```

## Runtime includes

```php
include($module . ".php");
```

## Hidden routers

```php
index.php?page=users
```

## Apache rewrite assumptions

`.htaccess`

## Cron scripts

```text
cron/
jobs/
scripts/
```

---

# 21. What Makes This Tool Truly Valuable

Not just parsing code.

The real value is:

## Architecture inference

AND

## Modernization decision intelligence

Anyone can scan PHP.

Very few tools can say:

> “This system can be incrementally modernized to Laravel in 6 phases with medium risk because module coupling is limited to reporting and auth.”

That’s the gold.

---

# 22. Recommended Tech Stack

## Parsing

* [nikic/PHP-Parser](https://github.com/nikic/PHP-Parser?utm_source=chatgpt.com)

## Static analysis inspiration

* [PHPStan](https://phpstan.org?utm_source=chatgpt.com)
* [Psalm](https://psalm.dev?utm_source=chatgpt.com)

## Graphing

* Neo4j
* Graphviz

## Rule engine

Custom DSL for modernization rules.

---

# 23. A Powerful Future Direction

Eventually your tool can evolve into:

## AI-assisted modernization orchestration

Where it can:

* understand architecture
* estimate migration risk
* generate adapters
* scaffold services
* generate tests
* produce migration pull requests

That becomes extremely valuable for enterprises maintaining legacy PHP monoliths.
