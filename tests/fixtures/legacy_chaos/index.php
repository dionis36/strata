<?php
// Entry point / Page Controller
include 'functions.php'; // Requirement 3B

$conn = connect_db();
$user = get_user($_GET['id']);

echo "<h1>Welcome " . $user['name'] . "</h1>";
include 'circular_a.php';
