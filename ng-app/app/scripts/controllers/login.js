'use strict';

angular.module('nereidProjectApp')
.controller('LoginCtrl', [
    '$scope',
    '$state',
    'nereidAuth',
    'Helper',
    function($scope, $state, nereidAuth, Helper) {
      if (nereidAuth.isLoggedIn()) {
        $state.go('base');
      }

      $scope.submit = function(form) {
        $scope.loggingIn = true;
        if (form.$invalid) {
          return;
        }
        nereidAuth.login($scope.user.email, $scope.user.password)
          .success(function(){
            $state.go('base');
          })
          .error(function(reason){
            Helper.showToast(reason.message, 5000);
          })
          .finally(function () {
            $scope.loggingIn = false;
          });
      };
    }
  ]);
