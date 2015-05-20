angular.module('nereidProjectApp')
.directive('globalSearch', function($timeout, $parse) {
  return {
    link: function(scope, element, attrs) {
      var model = $parse(attrs.globalSearch);
      var inputElement = angular.element(element[0]).find('input');
      scope.$watch(model, function(value) {
        if(value === true) {
          $timeout(function() {
            inputElement.focus();
          });
        }
      });

      // Listen to ESC and hide the global search
      inputElement.bind("keydown keypress", function (event) {
        if(event.which === 27) {
          scope.$parent.$apply(function(scope) {
            scope.showGlobalSearch=false;
          });
          scope.$apply(model.assign(scope, false));
          event.preventDefault();
        }
      });
    }
  };
});
