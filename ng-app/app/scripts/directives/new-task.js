'use strict';

angular.module('nereidProjectApp')
  .directive('createTask', [
    '$mdDialog',
    '$state',
    'Task',
    'Helper',
    function ($mdDialog, $state, Task, Helper) {
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
                $scope.subTypes = Task.subTypes;
                $scope.taskObj = {};

                $scope.submit = function() {
                  Task.create($scope.project.id, $scope.taskObj)
                    .success(function(result) {
                      Helper.showToast('Task ' + result.displayName + ' is created.');
                      $state.go('base.project.task', {projectId: result.parent, taskId: result.id});
                      $scope.hide();
                    })
                    .error(function(errors) {
                      $scope.errors = errors;
                      Helper.showToast('Error while trying to create new task. Please fill all required fields.');
                    });
                };
                $scope.hide = function() {
                  $mdDialog.cancel();
                };
              },
              templateUrl: 'views/create-task.html',
            });
          };

        }
      };
    }]);
