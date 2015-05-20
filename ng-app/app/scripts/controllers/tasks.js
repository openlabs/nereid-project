'use strict';

angular.module('nereidProjectApp')
.controller('TasksCtrl', [
    '$scope',
    '$state',
    function($scope, $state) {
      $scope.selectedIndex = $state.current.tabIndex;

      if(!$scope.selectedIndex) {
        $scope.selectedIndex = 0;
      }

      $scope.updateRoute = function(state) {
        $state.go('base.tasks.' + state);
      };

    }
  ]);
