'use strict';

angular.module('nereidProjectApp')
.controller('TasksCtrl', [
    '$scope',
    '$state',
    'Task',
    function($scope, $state, Task) {
      $scope.selectedIndex = $state.current.tabIndex;
      $scope.projectId = $state.params.projectId;
      $scope.progressStates = Task.progressStates;

      if(!$scope.selectedIndex) {
        $scope.selectedIndex = 0;
      }

      $scope.updateRoute = function(state) {
        $state.go('base.project.tasks.' + state);
      };

    }
  ]);
