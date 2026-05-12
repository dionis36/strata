<?php
// Entry point / Page Controller
include 'functions.php'; // Requirement 3B

$conn = connect_db();
$user = get_user($_GET['id']); // Trigger for RAW_SQL in functions.php

// Requirement 13: Custom Auth
session_start();
if (!isset($_SESSION['user'])) {
    header('Location: login.php');
}

// Requirement 12: Template Engine marker
$smarty->display('index.tpl');

echo "<h1>Welcome " . $user['name'] . "</h1>";
include 'circular_a.php';
