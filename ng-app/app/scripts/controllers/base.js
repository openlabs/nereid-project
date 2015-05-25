'use strict';

angular.module('nereidProjectApp')
.controller('BaseCtrl', [
    '$scope',
    'hotkeys',
    '$mdDialog',
    '$mdSidenav',
    function($scope, hotkeys, $mdDialog, $mdSidenav) {
      //TODO: Handle global search

      hotkeys.add({
        combo: '/',
        description: 'Display the search box',
        callback: function() {
          $scope.showGlobalSearch = true;
        }
      });

      var showJumpDialog = function() {
        $mdDialog.show({
          templateUrl: 'views/jump-to-dialog.html',
          escapeToClose: true,
          clickOutsideToClose: true,
          controller: 'ProjectsCtrl'
        });
      };

      hotkeys.add({
        combo: ['ctrl+k', 'command+k'],
        description: 'Jump to projects',
        callback: showJumpDialog
      });

      $scope.toggleLeft = function() {
        $mdSidenav('left').toggle();
      };

    }
  ]);
