'use strict';

angular.module('nereidProjectApp')
.controller('ProjectsCtrl', [
    '$mdDialog',
    '$scope',
    'Project',
    'Helper',
    function($mdDialog, $scope, Project, Helper) {
      $scope.page = 0;
      $scope.perPage = 50;
      $scope.projects = [];

      $scope.loadProjects = function(refresh) {
        if(refresh) {
          $scope.page = 0;
          $scope.perPage = 50;
          $scope.projects = [];
        }
        if($scope.pages === $scope.page) {
          return;
        }
        $scope.loadingProjects = true;
        Project.getProjects(++$scope.page, $scope.perPage)
          .success(function(result) {
            $scope.projects = $scope.projects.concat(result.items);
            $scope.pages = result.pages;
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch projects', reason);
          })
          .finally(function() {
            $scope.loadingProjects = false;
          });
      };

    }
  ]);
