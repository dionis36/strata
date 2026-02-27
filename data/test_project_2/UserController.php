<?php
class UserController
{
    public function showUser()
    {
        $db = new Database();
        $data = $db->connect();

        $view = new UserView();
        $view->render();
    }
}
