SnortWebApp = angular.module('SnortWeb', []);

SnortWebApp.config(function($interpolateProvider){
	$interpolateProvider.startSymbol('[[').endSymbol(']]');
});

SnortWebApp.controller('SnortWebController', function($scope, $http) {
	$http.get('get_pcaps').then(function(response) {
		$scope.pcap_list = response.data;
		$scope.selectedPcap = response.data[0].name
		$scope.selectedPcapId = response.data[0].id
	});
	$("#runRulesBtn").click(function() {
		$http.post('run_rules', {"pcap_id":$scope.selectedPcapId, "rules":$("#snortRules").val()}).then(function(response) {
			console.log(response.data);
			$scope.pcap_response = response.data
		});
	});
	$scope.updatePcap = function(pcapName, id) {
		$scope.selectedPcap = pcapName;
		$scope.selectedPcapId = id;
	}
	$scope.upload_pcap = function() {
		$scope.$apply(function() {
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
				$('#uploadPcapModal').modal('toggle');
				console.log(response)
				$scope.selectedPcap = response.filename
				$scope.pcap_list.push({"name":response.filename, "id":response.id})
			});
		});
	}
});
