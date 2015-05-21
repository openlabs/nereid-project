'use strict';

angular.module('nereidProjectApp')
  .directive('createTask', [
    '$mdDialog',
    'Task',
    function ($mdDialog, Task) {
      return {
        restrict: 'E',
        transclude: true,
        scope: {
          getProject: '&project'
        },
        template: '<ng-transclude ng-click="openNewTaskModal()"></ng-transclude>',
        link: function (scope) {
          scope.openNewTaskModal = function() {
            $mdDialog.show({
              controller: function createTaskCtrl($scope, $mdDialog){

                $scope.project = scope.getProject();
                $scope.taskObj = {};

                $scope.submit = function() {
                  Task.create($scope.project.id, $scope.taskObj);
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
