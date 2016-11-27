<?php



include 'includeHeaderLoginHacked.php';

echo "Here is the list";

?>
<div id="right">

<style>

table, td, .leaderboardsHeader {
	width: 590px;
    border: 1px dotted brown;
	border-radius: 3px;
	margin-left: -30px;
	padding: 2px 1px;
	color: #EEEE55;
}

#table1 {
	border: 0px;
}

.table2, .trow
{
	border: 0px solid gray;
	width: 350px;
}

</style>

<table id = "table1">

<?php

$servername = "localhost";
$username = ""; // username and password are left blank
$password = "";
$dbname = "ethicalHacking";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);
// Check connection
if ($conn->connect_error) {
	
	echo "connection failed! (This should not happen ...) ";
    die("Connection failed: ");
//	exit();
}

$sql = "SELECT * FROM `projectDB` LIMIT 10";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    // output data of each row
    while($row = $result->fetch_assoc()) {
		// readinglogs` (`id`, `lastname`, `date`, `startingtime`, `endingtime`, `duration`, `pages`)
        echo "<tr>";
		echo "<td>" . $row["id"] . "-   " . $row["form"]. " </td></tr>";
		
	}
} else {
    echo "0 results";
}
?>
</table>	

</div>

</body>
</html>