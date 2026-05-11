<?php

namespace Core\Database;

interface RepositoryInterface {
    public function find(int $id): ?object;
}

trait Timestampable {
    public function updateTimestamp(): void {
        $this->updatedAt = new \DateTime();
    }
}

abstract class BaseRepository implements RepositoryInterface {
    use Timestampable;
    
    protected string $table;
    
    public function __construct(string $table) {
        $this->table = $table;
    }
}

namespace App\Services;

use Core\Database\BaseRepository;
use Core\Database\RepositoryInterface;

class UserService extends BaseRepository {
    private array $users = [];
    
    public function __construct() {
        parent::__construct('users');
    }
    
    public function find(int $id): ?object {
        // Static call detection
        \App\Log\Logger::info("Searching for user $id");
        
        // Instantiation detection
        $user = new \stdClass();
        $user->id = $id;
        
        // Internal method call
        $this->updateTimestamp();
        
        return $user;
    }
}

class AuthManager {
    public function login(UserService $svc) {
        // External method call on injected service
        return $svc->find(1);
    }
}
