<?php 
require_once('include/header.php');
require_once('include/menu.php'); 


			print_menu('platform'); ?>
			<br/><br/><br/>
			<center>
			<a href="network_stats.php?a=12h">Last 12 Hours</a> | <a href="network_stats.php?a=1d">Daily</a> | <a href="network_stats.php?a=1w">Weekly</a> | <a href="network_stats.php?a=1m">Monthly</a> | <a href="network_stats.php?a=1y">Year</a>
			<br/><br/><br/>
			<?php
				$age = (isset($_GET['a'])) ? $_GET['a'] : '12h';
				$graphs = array('calls','chans', 'hlr_onlinereg','hlr_onlinenoreg');
				foreach ($graphs as &$g) {
					echo "<img src='graphs/$g-$age.png' /><br/><br/>";
				}
			?>
			</center>
		</div>
	</body>
</html>
