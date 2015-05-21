'use strict';

angular.module('nereidProjectApp', [
  'ui.router',
  'ngMaterial',
  'openlabs.angular-nereid-auth',
  'cfp.hotkeys',
  'infinite-scroll'
  ])
  .config(function($stateProvider, $urlRouterProvider, $mdThemingProvider) {
    $urlRouterProvider
      .when('', '/')
      .when('/', '/projects')
      .otherwise('/404');

    $stateProvider
      .state('login', {
        url: '/login',
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        publicAccess: true
      })

      .state('404', {
        url: '/404',
        templateUrl: 'views/404.html'
      })

      .state('base', {
        url: '/',
        templateUrl: 'views/base.html',
        controller: 'BaseCtrl'
      })

      .state('base.projects', {
        url: 'projects',
        views: {
          'main-view': {
            templateUrl: 'views/projects.html',
            controller: 'ProjectsCtrl'
          }
        }
      })

      .state('base.project', {
        url: 'projects/{projectId:int}',
        views: {
          'main-view': {
            templateUrl: 'views/project.html',
            controller: 'ProjectCtrl'
          }
        }
      })

      .state('base.project.tasks', {
        url: '/tasks',
        views: {
          'project-nav-view': {
            templateUrl: 'views/tasks.html',
            controller: 'TasksCtrl'
          }
        }
      })

      .state('base.project.task', {
        url: '/tasks/{taskId:int}',
        views: {
          'project-nav-view': {
            templateUrl: 'views/task.html',
            controller: 'TaskCtrl'
          }
        }
      })

      .state('base.project.tasks.open', {
        url: '/open',
        tabIndex: 0, // Tab index of the md-tab in tasks view
        views: {
          'task-tabs': {
            templateUrl: 'views/open-tasks.html',
            controller: 'OpenTasksCtrl'
          }
        }
      })

      .state('base.project.tasks.all', {
        url: '/all',
        tabIndex: 1,
        views: {
          'task-tabs': {
            templateUrl: 'views/all-tasks.html',
            controller: 'AllTasksCtrl'
          }
        }
      })

      .state('base.project.tasks.my', {
        url: '/my',
        tabIndex: 2,
        views: {
          'task-tabs': {
            templateUrl: 'views/my-tasks.html',
            controller: 'MyTasksCtrl'
          }
        }
      });

      $mdThemingProvider.theme('default')
      .primaryPalette('light-blue', {
        'default': '500'
      })
      .accentPalette('pink');
      $mdThemingProvider.theme('input', 'default')
      .primaryPalette('grey');
  })
  .run(['$rootScope', '$state', 'nereidAuth', function ($rootScope, $state, nereidAuth) {
    nereidAuth.refreshUserInfo(); // XXX: why?

    $rootScope.$on('$stateChangeSuccess', function(event, toState) {
      if (!toState.publicAccess && !nereidAuth.isLoggedIn()) {
        // Redirect to login page if viewing non public page and not logged-In.
        $state.go('login');
      }
    });

    $rootScope.$on('nereid-auth:loginRequired', function () {
      nereidAuth.logoutUser();
    });

    $rootScope.$on('nereid-auth:logout', function () {
      $state.go('login');
    });
  }]);
