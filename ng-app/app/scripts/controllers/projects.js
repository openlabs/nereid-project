'use strict';

angular.module('nereidProjectApp')
.controller('ProjectsCtrl', [
    '$q',
    '$mdDialog',
    '$scope',
    'Project',
    'Helper',
    '$state',
    function($q, $mdDialog, $scope, Project, Helper, $state) {
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

      $scope.getMatches = function(searchText) {
        var deferred = $q.defer();

        var result = [];
        searchText = searchText.toLowerCase();
        angular.forEach($scope.projects, function(project){
          if(project.name.toLowerCase().indexOf(searchText) !== -1){
            result.push(project);
          }
          deferred.resolve(result);
        });

        return deferred.promise;
      };

      $scope.goToProject = function(project) {
        $state.go('base.project', {projectId: project.id});
      };

    }
  ]);
