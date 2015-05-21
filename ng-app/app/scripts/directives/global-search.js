'use strict';

angular.module('nereidProjectApp')
.directive('globalSearch', function($timeout, $parse) {
  return {
    link: function(scope, element, attrs) {
      var model = $parse(attrs.globalSearch);
      $timeout(function() {
        var inputElement = angular.element(element[0]).find('input');

        // Listen to ESC and hide the global search
        inputElement.bind('keydown keypress', function (event) {
          if(event.which === 27) {
            scope.$parent.$apply(function(scope) {
              scope.showGlobalSearch=false;
            });
            scope.$apply(model.assign(scope, false));
            event.preventDefault();
          }
        });
      }, 0);
    }
  };
});
