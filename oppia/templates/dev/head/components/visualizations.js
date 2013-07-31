// Copyright 2012 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Directives for reusable data visualization components.
 *
 * @author sll@google.com (Sean Lip)
 */

oppia.directive('barChart', function() {
  return {
    restrict: 'E',
    scope: {chartData: '=', chartColors: '='},
    controller: function($scope, $element, $attrs) {
      var chart = new google.visualization.BarChart($element[0]);
      $scope.$watch($attrs.chartData, function(value) {
        value = $scope.chartData;
        if (!$.isArray(value)) {
          return;
        }
        var data = google.visualization.arrayToDataTable(value);
        var legendPosition = 'right';
        if ($attrs.showLegend == 'false') {
          legendPosition = 'none';
        }
        var options =  {
          title: $attrs.chartTitle,
          colors: $scope.chartColors,
          isStacked: true,
          width: $attrs.width,
          height: $attrs.height,
          legend: {position: legendPosition},
          hAxis: {gridlines: {color: 'transparent'}},
          chartArea: {width: $attrs.chartAreaWidth, left:0}
        };
        chart.draw(data, options);
      });
    }
  };
});

oppia.directive('stateGraphViz', function(explorationData, $filter) {
  // constants
  var w = 960,
      h = 1500,
      i = 0;
  var NODE_PADDING_X = 8;
  // The following variable must be at least 3.
  var MAX_NODE_LABEL_LENGTH = 20;

  var getTextWidth = function(text) {
    return 40 + Math.min(MAX_NODE_LABEL_LENGTH, text.length) * 5;
  };

  return {
    restrict: 'E',
    scope: {
      val: '=',
      nodeFill: '@',
      opacityMap: '=',
      forbidNodeDeletion: '@'
    },
    link: function(scope, element, attrs) {
      scope.truncate = function(text) {
        return $filter('truncate')(text, MAX_NODE_LABEL_LENGTH);
      };

      scope.$watch('val', function (newVal, oldVal) {
        // TODO(sll): This does not update if a state name is changed.
        if (newVal) {
          drawGraph(newVal.nodes, newVal.links, newVal.initStateId,
                    scope.nodeFill, scope.opacityMap, scope.forbidNodeDeletion);
        }
      });

      var vis = d3.select(element[0]).append('svg:svg')
          .attr('height', h)
          .attr('class', 'oppia-graph-viz')
        .append('svg:g')
          .attr('transform', 'translate(20,30)');

      function drawGraph(nodes, links, initStateId, nodeFill, opacityMap, forbidNodeDeletion) {
        // clear the elements inside of the directive
        vis.selectAll('*').remove();

        // Update the links
        var link = vis.selectAll('path.link')
            .data(links);

        vis.append('svg:defs').selectAll('marker')
            .data(['arrowhead'])
          .enter().append('svg:marker')
            .attr('id', String)
            .attr('viewBox', '0 0 10 10')
            .attr('refX', 10)
            .attr('refY', 5)
            .attr('markerWidth', 6)
            .attr('markerHeight', 4.5)
            .attr('orient', 'auto')
          .append('svg:path')
            .attr('d', 'M 0 0 L 10 5 L 0 10 z')
            .attr('fill', 'black');

        var linkEnter = link.enter().append('svg:g')
            .attr('class', 'link');

        linkEnter.insert('svg:path', 'g')
            .style('stroke-width', 3)
            .style('stroke', 'grey')
            .attr('opacity', 0.6)
            .attr('class', 'link')
            .attr('d', function(d) {
              var sourceWidth = getTextWidth(d.source.name);
              var targetWidth = getTextWidth(d.target.name);

              var sourcex = d.source.x0 + sourceWidth/2;
              var sourcey = d.source.y0 + 20;
              var targetx = d.target.x0 + targetWidth/2;
              var targety = d.target.y0 + 20;

              if (d.source == d.target) {
                return 'M' + sourcex + ' ' + sourcey;
              }

              var dx = targetx - sourcex,
                  dy = targety - sourcey;

              /* Fractional amount of truncation to be applied to the end of
                 each link. */
              var startCutoff = (sourceWidth/2)/Math.abs(dx);
              var endCutoff = (targetWidth/2)/Math.abs(dx);
              if (dx === 0 || dy !== 0) {
                startCutoff = (dx === 0) ? 20.0/Math.abs(dy) : Math.min(
                    startCutoff, 20.0/Math.abs(dy));
                endCutoff = (dx === 0) ? 20.0/Math.abs(dy) : Math.min(
                    endCutoff, 20.0/Math.abs(dy));
              }

              var dxperp = targety - sourcey,
                  dyperp = sourcex - targetx,
                  norm = Math.sqrt(dxperp*dxperp + dyperp*dyperp);
              dxperp /= norm;
              dyperp /= norm;

              var midx = sourcex + dx/2 + dxperp*20,
                  midy = sourcey + dy/2 + dyperp*20,
                  startx = sourcex + startCutoff*dx,
                  starty = sourcey + startCutoff*dy,
                  endx = targetx - endCutoff*dx,
                  endy = targety - endCutoff*dy;

              // Draw a quadratic bezier curve.
              return 'M' + startx + ' ' + starty + ' Q ' + midx + ' ' + midy +
                  ' ' + endx + ' ' + endy;
            })
            .attr('marker-end', function(d) {
              return (
                (d.source.x0 == d.target.x0 && d.source.y0 == d.target.y0) ?
                '' : 'url(#arrowhead)');
            });

        // Update the nodes
        // TODO(sll): Put a blue border around the current node.
        var node = vis.selectAll('g.node')
            .data(nodes, function(d) { return d.id; });

        var nodeEnter = node.enter().append('svg:g')
            .attr('class', 'node');

        // Add nodes to the canvas.
        nodeEnter.append('svg:rect')
            .attr('x', function(d) { return d.x0 - NODE_PADDING_X; })
            .attr('y', function(d) { return d.y0; })
            .attr('ry', function(d) { return 4; })
            .attr('rx', function(d) { return 4; })
            .attr('width', function(d) {
               return getTextWidth(d.name) + 2*NODE_PADDING_X; })
            .attr('height', function(d) { return 40; })
            .attr('class', function(d) {
              return d.hashId != END_DEST ? 'clickable' : null; })
            .style('stroke', 'black')
            .style('stroke-width', function(d) {
              return (d.hashId == initStateId || d.hashId == END_DEST) ? '3' : '2';
            })
            .style('fill', function(d) {
              if (nodeFill) {
                return nodeFill;
              } else {
                return (
                  d.hashId == initStateId ? 'olive' :
                  d.hashId == END_DEST ? 'green' :
                  d.reachable === false ? 'pink' :
                  'beige'
                );
              }
            })
            .style('opacity', function(d) {
              return opacityMap ? opacityMap[d.hashId] : 1.0;
            })
            .on('click', function (d) {
              if (d.hashId != END_DEST) {
                explorationData.getStateData(d.hashId);
                scope.$parent.$parent.stateId = d.hashId;
                $('#editorViewTab a[href="#stateEditor"]').tab('show');
              }
            })
            .append('svg:title')
            .text(function(d) { return d.name; });

        nodeEnter.append('svg:text')
            .attr('text-anchor', 'middle')
            .attr('x', function(d) { return d.x0 + (getTextWidth(d.name) / 2); })
            .attr('y', function(d) { return d.y0 + 25; })
            .text(function(d) { return scope.truncate(d.name); });

        if (!forbidNodeDeletion) {
          // Add a 'delete node' handler.
          nodeEnter.append('svg:rect')
              .attr('y', function(d) { return d.y0; })
              .attr('x', function(d) { return d.x0; })
              .attr('height', 20)
              .attr('width', 20)
              .attr('opacity', 0) // comment out this line to see the delete target
              .attr('transform', function(d) {
                return 'translate(' + (getTextWidth(d.name) - 15) + ',' + (+0) + ')'; }
              )
              .attr('stroke-width', '0')
              .style('fill', 'pink')
              .on('click', function (d) {
                if (d.hashId != initStateId && d.hashId != END_DEST) {
                  scope.$parent.openDeleteStateModal(d.hashId);
                }
              });

          nodeEnter.append('svg:text')
              .attr('text-anchor', 'right')
              .attr('dx', function(d) { return d.x0 + getTextWidth(d.name) -10; })
              .attr('dy', function(d) { return d.y0 + 10; })
              .text(function(d) {
                return (d.hashId != initStateId && d.hashId != END_DEST) ? 'x' : '';
              });
        }
      }
    }
  };
});