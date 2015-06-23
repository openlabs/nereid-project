'use strict';

angular.module('nereidProjectApp')
.controller('ChangePasswordCtrl', [
    '$scope',
    '$state',
    'User',
    'Helper',
    'nereidAuth',
    function($scope, $state, User, Helper, nereidAuth) {

      $scope.submit = function(form) {
        $scope.changingPassword = true;
        if (form.$invalid) {
          return;
        }
        User.changePassword($scope.user)
          .success(function(result){
            Helper.showToast(result.message, 5000);
            nereidAuth.logoutUser();
          })
          .error(function(reason){
            $scope.errors = reason.errors;
            if(reason.message) {
              Helper.showToast(reason.message, 5000);
            } else {
              Helper.showToast('Error occured!', 5000);
            }
          })
          .finally(function () {
            $scope.changingPassword = false;
          });
      };

    }
  ]);
