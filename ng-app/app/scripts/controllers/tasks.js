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
        // Select the opened tasks by default.
        $scope.selectedIndex = 0;
        $state.go('base.project.tasks.open');
      }

      $scope.updateRoute = function(state) {
        $state.go('base.project.tasks.' + state);
      };

    }
  ]);
