import { $, Shepherd, Vue } from 'src/vendor.js'

let tour = new Shepherd.Tour({
  defaults: {
    classes: 'shepherd-theme-dark',
    scrollTo: false
  }
})

// Change this to prompt tour again
tour.version = 0.2

global.tour = tour

tour.start = function() {
    var _start = tour.start
    return function() {
        if (this.getCurrentStep()) {
            //already started
            alert("You already started a tour.")
        } else {
            _start.call(this)
        }
    }
}()

tour.on('cancel', function () {
  global.gokart.touring = false
})

tour.addStep('welcome', {
  text: 'Would you like a tour of the Spatial Support System? If you exit now, you can always rerun the tour by clicking "Take Tour" in <b>System Settings</b>.',
  buttons: [
    {
      text: 'Exit',
      classes: 'shepherd-button-secondary',
      action: tour.cancel
    },
    {
      text: 'Next',
      action: tour.next
    }
  ]
}).addStep('map-controls', {
  text: 'At the top right are common map controls for setting a scale, going full-screen, zooming, and measuring lengths and areas.',
  attachTo: '#menu-scale left',
  when: {
    'before-show': function () {
        $("#menu-tab-layers-label").click()
        $("#layers-active-label").click()
    },
    'show': function () {
      global.gokart.map.animate({center:[116, -32]},{resolution:global.gokart.map.resolutions[9]})
    }
  }
}).addStep('map-search', {
    text: 'There is also a search box with support for coordinates and place names. <br/><b>Try out some of these!</b><ul><li>17 Dick Perry Avenue, Kensington</li><li>Upper Swan, Western Australia</li><li>32.00858S 115.53978E</li><li>115° 38′ 58.0″ E, 33° 20′ 52.8″ S</li><li>MGA 50 718776E 6190981N</li><li>MGA50 3816452</li><li>FD ET 79</li><li>PIL AF50</li></ul>',
    attachTo: '#map-search left'
}).addStep('toolbox', {
    text: 'There is also a tool box which contains lots of helpful tools, for example: weather outlook, measurement tools, etc.<br>You can click the "toolbox" button to expand the list of tools.',
    attachTo: '#toolbox_expand left',
    when:{
        'before-show': function () {
            global.gokart.toolbox.showTools = false
        },
    }
}).addStep('toolbox-expanded', {
    text: 'This panel lists all the tools you can use.',
    attachTo: '#deselect-tool left',
    beforeShowPromise:function(resolve,reject){
        return new Promise(function(resolve,reject){
            $("#toolbox_expand").click()
            var func = function() {
                if ($("#toolbox_tools").is(":visible")) {
                    resolve()
                } else {
                    setTimeout(func,10)
                }
            }
            setTimeout(func,10)
        })
    },
    when:{
    }
}).addStep('toolbox-select-measurelength', {
    text: 'You can click the tool "Measure Length" to choose it.',
    attachTo: '#MeasureLength left',
    when:{
    }
}).addStep('toolbox-measurelength-selected', {
    text: 'The tool "Measure Length" is chosed and ready to use.',
    attachTo: '#toolbox_tool left',
    beforeShowPromise:function(resolve,reject){
        return new Promise(function(resolve,reject){
            $("#MeasureLength").click()
            var func = function() {
                if ($("#toolbox_tool").is(":visible")) {
                    resolve()
                } else {
                    setTimeout(func,10)
                }
            }
            setTimeout(func,10)
        })
    },
    when:{
    }
}).addStep('menu', {
  text: 'To the left are the interactive panes for <b>Layers</b>, <b>Drawing Tools</b> and <b>Vehicle Tracking</b>, <b> Bushfire Report</b>.',
  attachTo: '#menu-tab-layers-label right',
  when:{
      'before-show':function() {
          global.gokart.toolbox.toggleTool(false)
      }
  }
}).addStep('layers', {
  text: 'The <b>Layers</b> pane lets you find, organise and print what is visible on the map.',
  attachTo: '#menu-tab-layers-label right',
}).addStep('catalogue', {
  text: 'The catalogue in <b>Browse Layers</b> lets you add more layers to the map. Layers can be found by typing into the search box.',
  attachTo: '#menu-tab-layers-label right',
  when: {
    'before-show': function () {
      $('#layers-catalogue-label').click()
    }
  }
}).addStep('catalogue-toggle', {
  text: 'Clicking a layer\'s switch will add it on top of other map layers.',
  attachTo: '#menu-tab-layers-label right',
  when: {
    'before-show': function () {
      $('#find-layer').val('tenure').change()
      Vue.nextTick(function () {
        $('#layers-catalogue-list .switch-input').click()
        $('#find-layer').val('land').change()
      })
    }
  }
}).addStep('active', {
  text: 'The map layers in <b>Active</b> lets you configure layers that are part of the current map.',
  attachTo: '#menu-tab-layers-label right',
  when: {
    'before-show': function () {
      $('#layers-active-label').click()
    }
  }
}).addStep('active-opacity', {
  text: 'Clicking a layer opens a configuration panel, from which you can adjust transparency and other settings.',
  attachTo: '#menu-tab-layers-label right',
  when: {
    'before-show': function () {
      if (!global.gokart.tracking.trackingMapLayer) {
          global.gokart.catalogue.onLayerChange(global.gokart.tracking.trackingLayer, true)
      } else if (global.gokart.active.isHidden(global.gokart.tracking.trackingMapLayer)) {
          global.gokart.active.toggleHidden(global.gokart.tracking.trackingMapLayer)
      }
      $('div[data-id="' + env.resourceTrackingLiveLayer + '"]').click()
      Vue.nextTick(function () {
        $('#layer-config input.layer-opacity').val(30).change()
      })
    }
  }
}).addStep('active-remove', {
  text: 'You can also drag and drop layers to reorder them, and remove a layer by clicking the red X.',
  attachTo: '#menu-tab-layers-label right',
  when: {
    'before-show': function () {
      // vue doesn't pickup <a> clicks from jquery, use dom method
      $('div[data-id="' + env.resourceTrackingLiveLayer + '"] a.remove-layer').get(0).click()
    }
  }
}).addStep('export', {
  text: 'Under <b>Save & Print</b>, you can save the current state of the map (position, layers and drawings), and load previous sessions.<br/>You can also perform a quick print of the displayed map region as JPG, geospatial PDF or GeoTIFF.',
  attachTo: '#menu-tab-layers-label right',
  when: {
    'before-show': function () {
      $('#layers-export-label').click()
    }
  }
}).addStep('annotations', {
  text: 'The <b>Drawing Tools</b> pane lets you draw features onto the map.',
  attachTo: '#menu-tab-annotations-label right',
  when: {
    'before-show': function () {
      $('#menu-tab-annotations-label').click()
    }
  }
}).addStep('annotations-text', {
  text: 'Some of the tools have additional configuration options. Text notes are even able to be resized.',
  attachTo: '#menu-tab-annotations-label right',
  when: {
    'before-show': function () {
      $('a[title="Text Note"]').get(0).click()
      Vue.nextTick(function () {
        $('textarea.notecontent').height(60).val('Like this one where you\ncan set the text of a note').get(0).click()
        // the click above should cache the feature image ready to place on map
        global.gokart.annotations.note.colour = "#f57900"
        global.gokart.annotations.colour = "#f57900"
        global.gokart.annotations.note.text = "Like this one where you\ncan set the text of a note"
      })
    }
  }
}).addStep('annotations-draw', {
  text: 'Clicking on the map will place a feature.',
  attachTo: '#menu-tab-annotations-label right',
  when: {
    'before-show': function () {
      Vue.nextTick(function () {
          var pixel = global.gokart.map.olmap.getPixelFromCoordinate(global.gokart.map.olmap.getView().getCenter())
          global.gokart.map.olmap.simulateEvent("pointermove",pixel[0],pixel[1])
          global.gokart.map.olmap.simulateEvent("pointerdown",pixel[0],pixel[1])
          global.gokart.map.olmap.simulateEvent("pointerup",pixel[0],pixel[1])
      })
    }
  }
}).addStep('tracking', {
  text: 'The Tracking pane is used to find and filter the vehicles displayed on the map.',
  attachTo: '#menu-tab-tracking-label right',
  when: {
    'before-show': function () {
      $('#menu-tab-tracking-label').click()
    }
  }
}).addStep('BushfireReport', {
  text: 'The bushfire report pane is used to find,filter and edit the bushfire report displayed on the map.',
  attachTo: '#menu-tab-bfrs-label right',
  when: {
    'before-show': function () {
      $('#menu-tab-bfrs-label').click()
    }
  }
}).addStep('finish', {
  text: 'And with that, we\'ve reached the end of the tour! The Spatial Support System will revert back to the pre-tour state when you click NEXT.',
  when: {
    'hide': function() {
      document.location.reload()
    }
  }
})

export default tour
