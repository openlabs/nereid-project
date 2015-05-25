'use strict';

angular.module('nereidProjectApp')
.controller('ProjectCtrl', [
    '$mdDialog',
    '$scope',
    '$state',
    'Project',
    'Helper',
    function($mdDialog, $scope, $state, Project, Helper) {

      $scope.projectId = $state.params.projectId;

      $scope.loadProject = function() {
        Project.get($scope.projectId)
          .success(function(result) {
            $scope.project = result;
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch project', reason);
          });
      };

    }
  ]);
