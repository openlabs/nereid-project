'use strict';

angular.module('nereidProjectApp')
.controller('LoginCtrl', [
    '$scope',
    '$state',
    'nereidAuth',
    function($scope, $state, nereidAuth) {
      if (nereidAuth.isLoggedIn()) {
        $state.go('base');
      }

      $scope.submit = function(form) {
        if (form.$invalid) {
          return;
        }
        nereidAuth.login($scope.user.email, $scope.user.password)
          .success(function(){
            $state.go('base');
          })
          .error(function(){
            // TODO: handle error.
          });
      };
    }
  ]);
