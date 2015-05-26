'use strict';

angular.module('nereidProjectApp')
.controller('IterationsCtrl', [
    '$scope',
    '$state',
    'Iteration',
    'Helper',
    function($scope, $state, Iteration, Helper) {

      $scope.loadIterations = function() {
        $scope.loadingIterations = true;
        Iteration.getAll()
          .success(function(result) {
            $scope.iterations = result.items;
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch iterations', reason);
          })
          .finally(function() {
            $scope.loadingIterations = false;
          });
      };

    }
  ]);
