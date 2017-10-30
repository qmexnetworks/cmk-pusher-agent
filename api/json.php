<?php
	# This file is part of CMK Pusher.
	# Copyright by Markus Plischke and Q-MEX Networks.  All rights reserved.
	#
	# CMK Pusher is free software;  you can redistribute it and/or modify it
	# under the  terms of the  GNU General Public License  as published by
	# the Free Software Foundation in version 2.
	#
	# CMK Pusher is  distributed in the hope that it will be useful, but
	# WITHOUT ANY WARRANTY; without even the implied warranty of
	# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
	# GNU General Public License for more details.
	#
	# CMK Pusher is a passive push service for Check_MK
	#
	# @author Markus Plischke <m.plischke@q-mex.net>
	# @company Q-MEX Networks http://www.q-mex.net
	include 'config.inc.php';
	header('Content-type: application/json');
	$jsondata = implode("", file('php://input'));
	$clean_data = False;
	
	function debug_log($message)
    {
        global $debug;
        if($debug)
        {
            file_put_contents('json.log', "Line: ".$message."\n", FILE_APPEND);
        }
    }
	
	function clean_client($client_name)
	{
		$client_name = preg_replace("/[^A-Za-z0-9.-]+/i", "", $client_name);
		return $client_name;
	}
	
	$data = json_decode($jsondata);
	
	if(trim($data->transaction->action) == "push")
	{
		$output = base64_decode($data->transaction->values->agentoutput);
        if(trim($data->transaction->compress))
		{
            $output = zlib_decode($output);
		}
		
		$client_name = clean_client($data->transaction->values->client_name);
		
		# check for md5sum, if not exiting its legacy (old Client)
		if(!empty($data->transaction->values->md5sum))
		{
			if(md5($output) == trim($data->transaction->values->md5sum))
			{
				debug_log("Checked MD5 Sum - OK");
				$clean_data = True;
			}
			else{
				debug_log("Checked MD5 Sum - ERROR");
				$clean_data = False;
			}
		}
		else{
			# Set Clean Data for old clients
			$clean_data = True;
			debug_log("Checked MD5 Sum - Old Client - ".trim($data->transaction->values->client_name));
		}
		
		if($clean_data)
		{
			# write data to file
			$openfile = fopen($spool_path.'/'.$client_name.'.dump','w+');
			$content = $output;
			# Add freshness check to file
			$content .= "<<<cmk_pusher>>>\n";
			$content .= "last_connect ".date("Y-m-d H:i:s")."\n";
			fwrite($openfile, $content);
			fclose($openfile);
		}
	}
?>
