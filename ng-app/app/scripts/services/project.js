'use strict';

angular.module('nereidProjectApp')
  .factory('Project', [
    '$http',
    'nereid',
    function ($http, nereid) {

    var Project = this;

    Project.getAll = function() {
      // Returns all projects.
      // TODO: This means going through all pages
      // For the moment just handle 50
      return Project.getProjects(1, 50);
    };

    Project.getProjects = function(page, per_page) {
      if (page === undefined) {
        page=1;
      }
      if (per_page === undefined) {
        per_page=20;
      }
      return $http.get(nereid.buildUrl(
        '/projects?page=' + page + '&per_page=' + per_page
      ));
    };

    Project.get = function(projectId) {
      return $http.get(nereid.buildUrl('/project-' + projectId));
    };

    Project.getTasks = function(projectId, filter) {
      filter = filter || {};
      return $http.get(nereid.buildUrl('/projects/' + projectId + '/tasks'), {params: filter});
    };

    return Project;
  }
]);
