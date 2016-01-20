// Ionic Starter App

// angular.module is a global place for creating, registering and retrieving Angular modules
// 'starter' is the name of this angular module example (also set in a <body> attribute in index.html)
// the 2nd parameter is an array of 'requires'
var url = 'http://192.168.0.138:6700';

angular.module('starter', ['ionic','ngCordova'])

.run(function($ionicPlatform) {
  $ionicPlatform.ready(function() {
    if(window.cordova && window.cordova.plugins.Keyboard) {
      // Hide the accessory bar by default (remove this to show the accessory bar above the keyboard
      // for form inputs)
      cordova.plugins.Keyboard.hideKeyboardAccessoryBar(true);

      // Don't remove this line unless you know what you are doing. It stops the viewport
      // from snapping when text inputs are focused. Ionic handles this internally for
      // a much nicer keyboard experience.
      cordova.plugins.Keyboard.disableScroll(true);
    }
    if(window.StatusBar) {
      StatusBar.styleDefault();
    }
  });
})

.controller('imageController', function($scope, $cordovaCamera, $cordovaFile,$http,$cordovaFileTransfer) {
    $scope.images = [];
    $scope.images_data = [];
    $scope.svmresult = "AU:0";
    $scope.cnnresult = "AU:1";
    $scope.emotionresult = "Happy";
    $scope.feedback = "None";

    $scope.addImage = function() {
	    // 2
	    var options = {
		    destinationType : Camera.DestinationType.DATA_URL,
		    sourceType : Camera.PictureSourceType.CAMERA, // Camera.PictureSourceType.PHOTOLIBRARY
		    allowEdit : false,
		    encodingType: Camera.EncodingType.JPEG,
		    popoverOptions: CameraPopoverOptions,
	    };
	
	    // 3
	    $cordovaCamera.getPicture(options).then(function(imageData) {
     
		    // 4
		    onImageSuccess(imageData);
     
		    function onImageSuccess(fileURI) {
                $scope.svmresult = "Pending ...";
                $scope.cnnresult = "Pending ...";
                $scope.emotionresult = "Pending ...";
                $scope.feedback = "Pending ...";
                //$scope.images_data = [fileURI];
				$scope.images = ['data:image/jpg;base64,'+fileURI];
                $http({
                        method: "POST",
                        //headers: headers,
                        url: url+'/pushImage',
                        params: {'image':fileURI},
                        timeout:20000
                        //params: {'data':JSON.stringify($scope.images_data[0])}

                })
                .success(function(data, status) {
                    $scope.svmresult = data['svm'];
                    $scope.cnnresult = data['cnn'];
                     $scope.emotionresult = data['emo'];
                     $scope.feedback = "Success";
                })
                .error(function(data, status) {
                    $scope.feedback ="Error:";
                });
			    //createFileEntry(fileURI);
		    }
     
		    function createFileEntry(fileURI) {
			    window.resolveLocalFileSystemURL(fileURI, copyFile, fail);
		    }
     
		    // 5
		    function copyFile(fileEntry) {
			    var name = fileEntry.fullPath.substr(fileEntry.fullPath.lastIndexOf('/') + 1);
			    var newName = makeid() + name;
     
			    window.resolveLocalFileSystemURL(cordova.file.dataDirectory, function(fileSystem2) {
				    fileEntry.copyTo(
					    fileSystem2,
					    newName,
					    onCopySuccess,
					    fail
				    );
			    },
			    fail);
		    }
		
		    // 6
		    function onCopySuccess(entry) {
			    $scope.$apply(function () {
                    //$scope.svmresult = scope.images_data[0];
				    //$scope.images = [scope.images_data[0]];
                   /* var option_list = {
                        fileKey: "avatar",
                        fileName: "Test.jpg",
                        chunkedMode: false,
                        mimeType: "image/jpg"
                    };
                    $("http://192.168.1.100:6700/pushImage", entry.nativeURL, option_list).then(function(result) {
                        $scope.feedback = "omg!!!" +JSON.stringify(result);
                    }, function(err) {
                        $scope.feedback = "nope";
                    }, function (progress) {
                        // constant progress updates
                        $scope.feedback = "progres!!!" +JSON.stringify(progress);
                    });*/
                  /* $http({
	                            method: "POST",
	                            //headers: headers,
                                url: url+'/pushImage',
                                params: {'image':$scope.images_data[0]},
                                timeout:20000
                                //params: {'data':JSON.stringify($scope.images_data[0])}

                        })
                            .success(function(data, status) {
                                $scope.svmresult = data['svm'];
                            })
                            .error(function(data, status) {
                                $scope.feedback ="Error:" +JSON.stringify(data);
                            });*/
			    });
		    }
     
		    function fail(error) {
			    console.log("fail: " + error.code);
		    }
     
		    function makeid() {
			    var text = "";
			    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
     
			    for (var i=0; i < 5; i++) {
				    text += possible.charAt(Math.floor(Math.random() * possible.length));
			    }
			    return text;
		    }
     
	    }, function(err) {
		    console.log(err);
	    });
    }
 
    $scope.urlForImage = function(imageName) {
      var name = imageName.substr(imageName.lastIndexOf('/') + 1);
      var trueOrigin = cordova.file.dataDirectory + name;
      return trueOrigin;
    }
});
