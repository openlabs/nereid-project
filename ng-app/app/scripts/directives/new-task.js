'use strict';

angular.module('nereidProjectApp')
  .directive('createTask', [
    '$mdDialog',
    function ($mdDialog) {
      return {
        restrict: 'E',
        transclude: true,
        scope: {},
        template: '<ng-transclude ng-click="openNewTaskModal()"></ng-transclude>',
        link: function (scope) {
          scope.openNewTaskModal = function() {
            $mdDialog.show({
              controller: function createTaskCtrl($scope, $mdDialog){
                $scope.submit = function() {
                  // TODO: handle form submit
                };
                $scope.hide = function() {
                  $mdDialog.cancel();
                };
              },
              templateUrl: 'views/create-task.html',
            })
            .then(function() {
              // Dialog hidden.
            }, function() {
              // Dialog canceled.
            });
          };

        }
      };
    }]);
