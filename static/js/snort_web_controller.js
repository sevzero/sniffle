SnortWebApp = angular.module('SnortWeb', []);

SnortWebApp.config(function($interpolateProvider){
	$interpolateProvider.startSymbol('[[').endSymbol(']]');
});

SnortWebApp.controller('SnortWebController', function($scope, $http, $timeout) {
	$http.get('get_pcaps').then(function(response) {
		$scope.pcap_list = response.data;
		$scope.selectedPcap = response.data[0].name;
		$scope.selectedPcapId = response.data[0].id;
	});
	$scope.runRules = function() {
		$scope.waiting_for_snort = true;
		$http.post('run_rules', {"pcap_id":$("#selectedPcap").val(), "rules":$("#snortRules").val()}).then(function(response) {
			$scope.pcap_response = response.data;
			$scope.waiting_for_snort = false;
		});
	}
	$scope.updatePcap = function(pcapName, id) {
		$scope.selectedPcap = pcapName;
		$scope.selectedPcapId = id;
	}
	$scope.load_rules = function() {
		var file = $("#rules-file-loader").prop("files")[0];
		var reader = new FileReader();
		reader.onload = function (e) {
			$("#snortRules").val(e.target.result);
		}
		reader.readAsText(file);
		$('#loadRulesModal').modal('toggle');
	}
	$scope.upload_pcap = function() {
		$.ajax({
			url: '/upload_pcap',
			type: 'POST',
			data: new FormData($('#pcap-upload-form')[0]),
			// Tell jQuery not to process data or worry about content-type
			// You *must* include these options!
			cache: false,
			contentType: false,
			processData: false,
			dataType: "json",
			headers: {"X-Remember": $("#savePermanently").prop("checked")},
			// Custom XMLHttpRequest
			xhr: function() {
				var myXhr = $.ajaxSettings.xhr();
				if (myXhr.upload) {
					// For handling the progress of the upload
					myXhr.upload.addEventListener('progress', function(e) {
						if (e.lengthComputable) {
							$('progress').attr({
								value: e.loaded,
								max: e.total,
							});
						}
					} , false);
				}
				return myXhr;
			}
		}).done(function(response){
			$scope.$apply(function() {
				$scope.selectedPcap = response.filename
				if ($scope.pcap_list.slice(-1)[0]["id"].startsWith("tmp_"))
					$scope.pcap_list.pop();
				$scope.pcap_list.push({"name":response.filename, "id":response.id})
				$('#uploadPcapModal').modal('toggle');
			});
			$timeout(function() { $("#selectedPcap").find('option[value="' + response.id + '"]').prop("selected", true); });
		});
	}
});
