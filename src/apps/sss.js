import {

  $,
  svg4everybody,
  ol,
  proj4,
  moment,
  localforage,
  Vue,
  VueStash,
  utils
} from 'src/vendor.js'
import App from './sss.vue'
import tour from './sss-tour.js'
import profile from './sss-profile.js'
import gokartListener from './gokart-listener.js'

//merge _env into env
if (global._env) {
    $.each(global._env,function(key,value){env[key] = value})

    global._env = undefined
}

global.tour = tour
//Return an environment dependent layer id
global.getLayerId = function(id) {
    return (env && env.layerMapping && env.layerMapping[id]) || id
}
global.isKbLayer = function(id) {
    return typeof id === "string" && id.startsWith("kaartdijin-boodja")
}
global.getLayerUrl = function(layer_id, env) {
  if (isKbLayer(layer_id) || layer_id.startsWith("dpaw:bushfire")) {
      return env.kbService;
  } else if (layer_id.startsWith("hotspots:")) {
      return env.hotspotsUrl + "/wfs";
  } else {
      return env.kmiService;
  }
},
//sometimes we use a different layer to get the detail layer information.
global.getDetailLayerId = function(id) {
    return (env && env.detailLayerMapping && env.detailLayerMapping[id]) || (env && env.layerMapping && env.layerMapping[id]) || id
}
//Return an environment independent layer id
global.getIndependentLayerId = function(id) {
    if (!env || !env.layerMapping) {
        return id
    } 
    var independentId = id
    $.each(env.layerMapping,function(key,value){
        if (value === id) {
            independentId = key
            return false
        }
    })
    return independentId
}
global.getAppId = function(id) {
    return (env && env.appMapping && env.appMapping[id]) || id
}

global.debounce = function (func, wait, immediate) {
  // Returns a function, that, as long as it continues to be invoked, will not
  // be triggered. The function will be called after it stops being called for
  // N milliseconds. If `immediate` is passed, trigger the function on the
  // leading edge, instead of the trailing.
  'use strict'
  var timeout
  return function () {
    var context = this
    var args = arguments
    var later = function () {
      timeout = null
      if (!immediate) func.apply(context, args)
    }
    var callNow = immediate && !timeout
    clearTimeout(timeout)
    timeout = setTimeout(later, (context && context.wait) || wait)
    if (callNow) func.apply(context, args)
  }
}
var volatileData = {
  // overridable defaults for WMTS and WFS loading
  appType:env.appType,
  // fixed scales for the scale selector (1:1K increments)
  fixedScales: [0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 80, 100, 125, 250, 500, 1000, 2000, 3000, 5000, 10000, 25000],
  // default matrix from KMI
  resolutions: [0.17578125, 0.087890625, 0.0439453125, 0.02197265625, 0.010986328125, 0.0054931640625, 0.00274658203125, 0.001373291015625, 0.0006866455078125, 0.0003433227539062, 0.0001716613769531, 858306884766e-16, 429153442383e-16, 214576721191e-16, 107288360596e-16, 53644180298e-16, 26822090149e-16, 13411045074e-16],
  mmPerInch: 25.4,
  displayResolution:[1,1],
  whoami: { email: null },
  layout:{
      screenHeight:0,
      hintsHeight:0,
      screenWidth:0,
      leftPanelHeadHeight:90,
  },
  activeMenu:null,
  activeSubmenu:null,
  hints:null,
  showHints:false,
  // filters for finding layers
  catalogueFilters: [
    ['basemap', 'Base Imagery'],
    ['boundaries', 'Admin Boundaries'],
    ['communications', 'Communications'],
    ['fire', 'Fire Operations'],
    ['meteorology', 'Meteorology'],
    ['vegetation', 'Vegetation'],
    ['tenure', 'Tenure and Land Use'],
    ['infrastructure', 'Infrastructure'],
    ['grid', 'Grid Systems'],
    ['resources', 'Resource Tracking']
  ],
  matrixSets: {
    'EPSG:4326': {
      '1024': {
        'name': 'gda94',
        'minLevel': 0,
        'maxLevel': 17
      }
    }
  }
}

var systemSettings = {
  tourVersion: null,
  undoLimit:0,
  lengthUnit:"km",
  areaUnit:"ha",
  measureFeature:false,
  print:{
      retainBoundingbox:true,
      snapToFixedScale:true,
  },
  overviewMap:true,
  hoverInfo:false,
  resourceLabels:true,
  resourceDirections: true,
  viewportOnly: false,
  rightHandTools: true,
  graticule:true,
  bfrs:{
      bushfireLabels:true,
      viewportOnly: false,
  },
  weatheroutlook:{
      "weather-outlook-customized":null,
      "weather-outlook-amicus":null
  }
}

var persistentData = {
  view: {
    center: [123.75,  -24.966],
    scale:4026092
  },
  // id followed by properties to merge into catalogue
  activeLayers: [
    [env.resourceTrackingLiveLayer, {}],
    [env.stateMapLayer, {}]
  ],
  // blank annotations
  annotations: {
    type: 'FeatureCollection',
    features: []
  },
  drawingLogs: [],
  redoPointer: 0, //pointer to the next redo log 
  drawingSequence: 0,

  //data in settings will survive across reset
  settings:JSON.parse(JSON.stringify(systemSettings))
}
global.gokartService = env.gokartService;

global.localforage = localforage
global.$ = $

var resetRe = new RegExp('^\\?([^?]*&)?reset=true(&.*)?$','i')
var result = resetRe.exec(window.location.search)
if (result) {
    localforage.setItem('sssOfflineStore', {}).then(function (v) {
        var searchString = (result[1]?result[1]:"") + ((result[2] && result[2].length > 1)?result[2].substring(1):"")
        document.location.search = (searchString.length === 0)?"":("?" + (result[1]?result[1]:"") + ((result[2] && result[2].length > 1)?result[2].substring(1):""))
    })
} else {
    Vue.use(VueStash)
    localforage.getItem('sssOfflineStore').then(function (store) {
      if (store && store["activeLayers"] && store["activeLayers"].length === 0) {
          delete store["activeLayers"]
      }
      var storedData = utils.extend(JSON.parse(JSON.stringify(persistentData)), store || {}, volatileData)
      storedData['activeLayers'] = storedData['activeLayers'].filter(function(layer) {
        var layerId = layer && layer[0]
        return typeof layerId === 'string' && !layerId.includes("resource_tracking_history")
      })

      // If view values are invalid (e.g. due to a mobile browser bug),
      // fall back to defaults to prevent a crash on load.
      if (!Array.isArray(storedData.view.center) || storedData.view.center.length !== 2 || !Number.isFinite(storedData.view.center[0]) || !Number.isFinite(storedData.view.center[1])) {
        storedData.view.center = persistentData.view.center.slice()
      }
      if (!Number.isFinite(storedData.view.scale) || storedData.view.scale <= 0) {
        storedData.view.scale = persistentData.view.scale
      }

      global.gokart = new Vue({
        el: 'body',
        components: {
          App
        },
        data: {
          // store contains state we want to reload/persist
          store: storedData,
          pngs: {},
          fixedLayers:[],
          saved: null,
          touring: false,
          menuRevision:1,
          tints: {
            'selectedPoint': [['#b43232', '#2199e8']],
            'selectedDivision': [['#000000', '#2199e8'], ['#7c3100','#2199e8'], ['#ff6600', '#ffffff']],
            'selectedRoadClosurePoint': [['#000', '#2199e8']],
            'selectedPlusIcon': [['#006400', '#2199e8']],
          }
        },
        computed: {
          loading: function () { return this.$refs.app.$refs.loading },
          dialog: function () { return this.$refs.app.$refs.dialog },
          map: function () { return this.$refs.app.$refs.map },
          scales: function () { return this.$refs.app.$refs.map.$refs.scales },
          search: function () { return this.$refs.app.$refs.map.$refs.search },
          featuredetail: function () { return this.$refs.app.$refs.map.$refs.featuredetail },
          weatherforecast: function () { return this.$refs.app.$refs.map.$refs.weatherforecast },
          toolbox: function () { return this.$refs.app.$refs.map.$refs.toolbox },
          measure: function () { return this.$refs.app.$refs.map.$refs.measure },
          info: function() { return this.$refs.app.$refs.map.$refs.info},
          active: function () { return this.$refs.app.$refs.layers.$refs.active },
          layers: function () { return this.$refs.app.$refs.layers },
          catalogue: function () { return this.$refs.app.$refs.layers.$refs.catalogue },
          export: function () { return this.$refs.app.$refs.layers.$refs.export },
          annotations: function () { return this.$refs.app.$refs.annotations },
		      tracking: function () { return this.$refs.app.$refs.tracking },
		      thermal: function () { return this.$refs.app.$refs.thermal },
          settings: function () { return this.$refs.app.$refs.settings },
          systemsetting: function () { return this.$refs.app.$refs.settings.$refs.systemsetting },
          bfrs: function () { return this.$refs.app.$refs.bfrs },
          weatheroutlook: function () { return this.$refs.app.$refs.settings.$refs.weatheroutlook },
          geojson: function () { return new ol.format.GeoJSON() },
          //wgs84Sphere: function () { return new ol.sphere(6378137) },
          profile: function(){return profile},
          app: function() {return "SSS"},
          utils: function() {return utils},
          env:function() {return env},
          persistentData:function() {
              return utils.extract(persistentData,this.store)
          },
          tourVersion:function() {
              return this.store.settings.tourVersion
          },
          defaultSettings:function() {
              return systemSettings
          },
          screenHeight:function() {
              return this.store.layout.screenHeight
          },
          hints:function() {
              return this.store.hints
          },
          activeModule:function() {
             return this.store.activeSubmenu || this.store.activeMenu
          },
          isShowHints:function() {
              return this.store.showHints && this.store.hints
          },
          hasHints:function() {
              return this.store.hints
          },
        },
        watch: {
            tourVersion:function(newValue, oldValue) {
                if (newValue !== tour.version) {
                  this.takeTour()
                }
            },
          'store.view.center': function(newValue, oldValue) {
            if (!Array.isArray(newValue) || newValue.length !== 2 || !Number.isFinite(newValue[0]) || !Number.isFinite(newValue[1])) {
              this.store.view.center = persistentData.view.center.slice()
            }
          },
          'store.view.scale': function(newValue, oldValue) {
            if (!Number.isFinite(newValue) || newValue <= 0) {
              this.store.view.scale = persistentData.view.scale
            }
          },
            hints:function(newValue, oldValue) {
                var vm = this
                this.$nextTick(function(){
                    vm.setHintsHeight()
                })
            },
            menuRevision:function(newValue, oldValue) {
                var vm = this
                //var module = this.store.activeSubmenu || this.store.activeMenu
                //if (this[module]["adjustHeight"]) {
                //    this[module]["adjustHeight"]()
                //}
                this.$nextTick(function(){
                    vm.store.layout.leftPanelHeadHeight = $("#" + vm.activeModule + "-tabs").height() || 90
                    vm.setHintsHeight()
                })
            },
            screenHeight:function(newValue, oldValue) {
                var module = this.store.activeSubmenu || this.store.activeMenu
                if (this[module]["adjustHeight"]) {
                    this[module]["adjustHeight"]()
                }
                this.loading.adjustHeight()
            }
        },
        methods: {
          setHintsHeight:function() {
            if (this[this.activeModule]["adjustHeight"]) {
                this.store.layout.hintsHeight = (this.isShowHints?$("#hints").height():0) + (this.hasHints?32:0)
                this[this.activeModule]["adjustHeight"]()
            }
          },
          menuChanged:function() {
              this.menuRevision += 1
          },
          takeTour: function() {
              this.store.settings.tourVersion = tour.version
              this.export.saveState()
              this.touring = true
              tour.start()
          },
          setHints:function() {
              this.store.hints = null
              this.store.showHints = false
              var module = this.store.activeSubmenu || this.store.activeMenu
              if (module && this[module]) {
                if (arguments.length === 0 ) {
                    this.store.hints = null
                } else if (arguments.length === 1) {
                    this.store.hints = arguments[0]
                } else {
                    this.store.hints = arguments
                }
              }
          },
          getCookie:function(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(";").shift();
            return null;
          },
          setCookie:function(name, value, days = 365) {
            const date = new Date();
            date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
            document.cookie = `${name}=${value}; expires=${date.toUTCString()}; path=/`;
          },
          checkAndUpdateCookie:function() {
            const COOKIE_NAME = "sss_version";
            const CURRENT_VERSION = env.sssVersion;

            const cookieVersion = this.getCookie(COOKIE_NAME);

            if (!cookieVersion || cookieVersion !== CURRENT_VERSION) {
              // Either cookie is missing OR version mismatch
              console.log("Cookie missing or version mismatch. Updating cookie and resetting SSS");
              this.setCookie(COOKIE_NAME, CURRENT_VERSION);
                //except settings, clear everything
                localforage.setItem('sssOfflineStore', {settings:this.$root.persistentData.settings}).then(function (v) {
                  document.location.reload()
                })
            }
        },
      },
        ready: function () {
          this.checkAndUpdateCookie();
          var self = this
          self.loading.app.phaseBegin("initialize", 20, "Initialize")
          // setup foundation, svg url support
          $(document).foundation()
          svg4everybody()
          // set title
          $('title').text(profile.description)
          // calculate screen res
          // Use visibility:hidden + position:absolute instead of display:none,
          // because some mobile browsers (e.g. iOS Safari) return 0 for .width()
          // on display:none elements, which would make dpmm=0 and break getScale().
          $('body').append('<div id="dpi" style="width:1in;visibility:hidden;position:absolute"></div>')
          self.dpi = parseFloat($('#dpi').width())
          self.store.dpmm = (self.dpi && self.dpi > 0) ? self.dpi / self.store.mmPerInch : 96 / self.store.mmPerInch
          $('#dpi').remove();
          // get user info - store the deferred so gk-init can wait for it
          self._whoamiDeferred = (function () {
            return $.ajax({
                url: self.env.authUrl || "/sso/auth",
                method:"GET",
                dataType:"json",
                success: function (response, stat, xhr) {
                    $.extend(self.store.whoami, response)
                },
                error: function (xhr, status, message) {
                    alert("Get user profile failed.  " + status + " : " + (xhr.responseText || message))
                },
                xhrFields: {
                  withCredentials: true
                }
            })
          })()
          // bind menu side-tabs to reveal the side pane
          var offCanvasLeft = $('#offCanvasLeft')
          $('#menu-tabs').on('change.zf.tabs', function (ev) {
            offCanvasLeft.addClass('reveal-responsive')
            self.map.olmap.updateSize()
          }).on('click', '.tabs-title a[aria-selected=false]', function (ev) {
            offCanvasLeft.addClass('reveal-responsive')
            $(this).attr('aria-selected', true)
            self.map.olmap.updateSize()
          }).on('click', '.tabs-title a[aria-selected=true]', function (ev) {
            offCanvasLeft.toggleClass('reveal-responsive')
            self.map.olmap.updateSize()
          })
          $('#side-pane-close').on('click', function (ev) {
            offCanvasLeft.removeClass('reveal-responsive')
            $('#menu-tabs').find('.tabs-title a[aria-selected=true]').attr('aria-selected', false)
            self.map.olmap.updateSize()
          })
    
          // pack-in catalogue
		  self.fixedLayers = self.fixedLayers.concat([{
          /*
            type: 'TileLayer',
            name: 'Firewatch Hotspots 72hrs',
            id: 'landgate:firewatch_ecu_hotspots_last_0_72',
            format: 'image/png',
            refresh: 60
          }, {
          */
            type: 'TimelineLayer',
            name: 'Himawari-8 Hotspots',
            id: 'himawari8:hotspots',
            params: {
              FORMAT: 'image/png'
            },
            timelineRefresh:300,
            fetchTimelineUrl:function(lastUpdatetime){
                return '/hi8/AHI_TKY_FHS?updatetime=' + lastUpdatetime
            },
            setTimeIndex:function(layer, tileLayer, previousTimeline, defaultFunc) {
                var timeIndex = null
                if (previousTimeline && previousTimeline.length > 1 && tileLayer.get('timeIndex') && tileLayer.get('timeIndex') < previousTimeline.length && tileLayer.get('timeIndex') >= 1) {
                    timeIndex = tileLayer.get('timeIndex')
                }
                if (timeIndex == null || timeIndex == previousTimeline.length - 1) {
                    var newTimeIndex = layer.timeline.length - 1
                    if (previousTimeline && previousTimeline[timeIndex][0] === layer.timeline[newTimeIndex][0]) {
                        tileLayer.set('timeIndex', layer.timeline.length - 1, true)
                    } else {
                        tileLayer.set('timeIndex', layer.timeline.length - 1)
                    }
                } else {
                    var newTimeIndex = layer.timeline.findIndex(function(o) {return o[0] === previousTimeline[timeIndex][0]})
                    if (newTimeIndex >= 0) {
                        tileLayer.set('timeIndex', newTimeIndex, true)
                    } else {
                        defaultFunc(layer, tileLayer, previousTimeline)
                    }
                }
            }
          }, {
            type: 'TimelineLayer',
            name: 'Himawari-8 True Colour',
            id: 'himawari8:bandtc',
            timelineRefresh:300,
            fetchTimelineUrl:function(lastUpdatetime){
              return '/hi8/AHI_TKY_b321?updatetime=' + lastUpdatetime
            },
            setTimeIndex:function(layer,tileLayer,previousTimeline,defaultFunc) {
                var timeIndex = null
                if (previousTimeline && previousTimeline.length > 1 && tileLayer.get('timeIndex') && tileLayer.get('timeIndex') < previousTimeline.length && tileLayer.get('timeIndex') >= 1) {
                    timeIndex = tileLayer.get('timeIndex')
                }
                if (timeIndex == null || timeIndex == previousTimeline.length - 1) {
                    var newTimeIndex = layer.timeline.length - 1
                    if (previousTimeline && previousTimeline[timeIndex][0] === layer.timeline[newTimeIndex][0]) {
                        tileLayer.set('timeIndex',layer.timeline.length - 1,true)
                    } else {
                        tileLayer.set('timeIndex',layer.timeline.length - 1)
                    }
                } else {
                    var newTimeIndex = layer.timeline.findIndex(function(o) {return o[0] === previousTimeline[timeIndex][0]})
                    if (newTimeIndex >= 0) {
                        tileLayer.set('timeIndex',newTimeIndex,true)
                    } else {
                        defaultFunc(layer,tileLayer,previousTimeline)
                    }
                }
            }
            //base: true
          /*
          }, {
            type: 'TimelineLayer',
            name: 'Himawari-8 Band 3',
            id: 'himawari8:band3',
            timelineRefresh:300,
            fetchTimelineUrl:function(lastUpdatetime){
                return self.env.gokartService + '/hi8/AHI_TKY_b3?updatetime=' + lastUpdatetime
            }
            base: true
          */
          }, {
            type: 'TimelineLayer',
            name: 'Himawari-8 Band 7',
            id: 'himawari8:band7',
            timelineRefresh:300,
            fetchTimelineUrl:function(lastUpdatetime){
                return '/hi8/AHI_TKY_b7?updatetime=' + lastUpdatetime
            },
            setTimeIndex:function(layer,tileLayer,previousTimeline,defaultFunc) {
                var timeIndex = null
                if (previousTimeline && previousTimeline.length > 1 && tileLayer.get('timeIndex') && tileLayer.get('timeIndex') < previousTimeline.length && tileLayer.get('timeIndex') >= 1) {
                    timeIndex = tileLayer.get('timeIndex')
                }
                if (timeIndex == null || timeIndex == previousTimeline.length - 1) {
                    var newTimeIndex = layer.timeline.length - 1
                    if (previousTimeline && previousTimeline[timeIndex][0] === layer.timeline[newTimeIndex][0]) {
                        tileLayer.set('timeIndex',layer.timeline.length - 1,true)
                    } else {
                        tileLayer.set('timeIndex',layer.timeline.length - 1)
                    }
                } else {
                    var newTimeIndex = layer.timeline.findIndex(function(o) {return o[0] === previousTimeline[timeIndex][0]})
                    if (newTimeIndex >= 0) {
                        tileLayer.set('timeIndex',newTimeIndex,true)
                    } else {
                        defaultFunc(layer,tileLayer,previousTimeline)
                    }
                }
            }
          }, {
            type: 'TileLayer',
            id: env.stateMapLayer,
            base: true
          },
            //base: true
         /*
          }, {
            type: 'TimelineLayer',
            name: 'Himawari-8 Band 15',
            id: 'himawari8:band15',
            source: self.env.gokartService + '/hi8/AHI_TKY_b15',
            refresh: 300,
            //base: true
          }, {
            type: 'TileLayer',
            name: 'State Map Base',
            id: env.stateMapLayer,
            //base: true
          }, {
            type: 'TileLayer',
            name: 'Virtual Mosaic',
            id: 'landgate:LGATE-V001',
            //base: true
          }, {
            type: 'TileLayer',
            name: 'DFES Active Fireshapes',
            id: 'landgate:dfes_active_fireshapes',
            refresh: 60
          */
          /*}, {
            type: 'TileLayer',
            name: 'Forest Fire Danger Index',
            id: 'bom:forest_fire_danger_index',
            timelineRefresh:300,
            fetchTimelineUrl:function(lastUpdatetime){
                return "/bom/IDZ71117?basetimelayer=bom:IDZ71117_datetime&timelinesize=72&layertimespan=3600&updatetime=" + lastUpdatetime
            }*/
      // {
      //       type: 'TileLayer',
      //       name: 'Forest Fire Danger Index',
      //       id: 'bom:forest_fire_danger_index',
      //       timelineRefresh: 300,
      //       fetchTimelineUrl: function(lastUpdatetime){
      //           //return "/bom/IDZ71117?basetimelayer=bom:IDZ71117_datetime&timelinesize=72&layertimespan=3600&updatetime=" + lastUpdatetime
			// 	return "/bom/IDZ71117?basetimelayer=bom:IDZ71117_datetime&timelinesize=72&layertimespan=3600&updatetime=" + lastUpdatetime
      //       }
      //     }, {
      //       type: 'TileLayer',
      //       name: 'Maximum Forest Fire Danger Index',
      //       id: 'bom:maximum_forest_fire_danger_index',
      //       timelineRefresh:300,
      //       fetchTimelineUrl:function(lastUpdatetime){
      //           return "/bom/IDZ71118?basetimelayer=bom:IDZ71118_datetime&timelinesize=4&layertimespan=86400&updatetime=" + lastUpdatetime
      //       }
      //     }, {
      //       type: 'TileLayer',
      //       name: 'Grassland Fire Danger Index',
      //       id: 'bom:grass_fire_danger_index',
      //       timelineRefresh:300,
      //       fetchTimelineUrl:function(lastUpdatetime){
      //           return "/bom/IDZ71122?basetimelayer=bom:IDZ71122_datetime&timelinesize=72&layertimespan=3600&updatetime=" + lastUpdatetime
      //       }
      //     }, {
      //       type: 'TileLayer',
      //       name: 'Maximum Grassland Fire Danger Index',
      //       id: 'bom:maximum_grass_fire_danger_index',
      //       timelineRefresh:300,
      //       fetchTimelineUrl:function(lastUpdatetime){
      //           return "/bom/IDZ71123?basetimelayer=bom:IDZ71123_datetime&timelinesize=4&layertimespan=86400&updatetime=" + lastUpdatetime
      //       }
      //     }, {
      //       type: 'TileLayer',
      //       name: 'Continuous Haines',
      //       id: 'bom:continuous_haines',
      //       timelineRefresh:300,
      //       fetchTimelineUrl:function(lastUpdatetime){
      //           return "/bom/IDZ71115?basetimelayer=bom:IDZ71115_datetime&timelinesize=56&layertimespan=10800&updatetime=" + lastUpdatetime
      //       }
      //     }
		  /*, {
            type: 'TileLayer',
            name: 'mslp',
            id: 'bom:mslp',
            timelineRefresh:300,
            fetchTimelineUrl:function(lastUpdatetime){
                return "/bom/IDY25300mslp?basetimelayer=bom:IDY25300_datetime&timelinesize=73&layeridpattern=IDY25300{:0>3}mslp&layertimespan=3600&updatetime=" + lastUpdatetime
            }
          }*/
		  ])
    
          // load custom annotation tools
    
          var sssTools = [
            {
              name: 'Fire Boundary',
              icon: '/static/dist/static/images/iD-sprite.svg#icon-area',
              style: self.annotations.getVectorStyleFunc(self.tints),
              selectedFillColour:[0, 0, 0, 0.25],
              fillColour:[0, 0, 0, 0.25],
              size:2,
              interactions: [self.annotations.polygonDrawFactory()],
              scope:["annotation"],
              showName: true,
              measureLength:true,
              measureArea:true,
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Draw a fire boundary on map ",
                        "Hold down the 'SHIFT' key during drawing to enable freehand mode. "
                    ]
                }
              ]
            },
            self.annotations.ui.defaultText,
            {
              name: 'Division',
              icon: '/static/dist/static/symbols/fire/division.svg',
              tints: self.tints,
              perpendicular: true,
              interactions: [self.annotations.pointDrawFactory(), self.annotations.snapToLineFactory()],
              style: self.annotations.getIconStyleFunction(self.tints),
              sketchStyle: self.annotations.getIconStyleFunction(self.tints),
              selectedTint: 'selectedDivision',
              scope:["annotation"],
              showName: true,
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Place a 'Division' in map."
                    ]
                }
              ]
            }, {
              name: 'Sector',
              icon: '/static/dist/static/symbols/fire/sector.svg',
              tints: self.tints,
              perpendicular: true,
              interactions: [self.annotations.pointDrawFactory(), self.annotations.snapToLineFactory()],
              style: self.annotations.getIconStyleFunction(self.tints),
              sketchStyle: self.annotations.getIconStyleFunction(self.tints),
              selectedTint: 'selectedDivision',
              scope:["annotation"],
              showName: true,
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Place a 'Sector' in map."
                    ]
                }
              ]
            },{
            /*  name: 'Hot Spot',
              icon: 'fa-circle red',
              interactions: [hotSpotDraw],
              style: hotSpotStyle,
              showName: true
            }, {*/
              name: 'Origin Point',
              icon: '/static/dist/static/symbols/fire/origin.svg',
              tints: self.tints,
              interactions: [self.annotations.pointDrawFactory()],
              style: self.annotations.getIconStyleFunction(self.tints),
              sketchStyle: self.annotations.getIconStyleFunction(self.tints),
              selectedTint: 'selectedPoint',
              scope:["annotation"],
              showName: true,
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Place a 'Origin Point' in map."
                    ]
                }
              ]
            }, {
              name: 'Spot Fire',
              icon: '/static/dist/static/symbols/fire/spotfire.svg',
              tints: self.tints,
              interactions: [self.annotations.pointDrawFactory()],
              style: self.annotations.getIconStyleFunction(self.tints),
              sketchStyle: self.annotations.getIconStyleFunction(self.tints),
              selectedTint: 'selectedPoint',
              scope:["annotation"],
              showName: true,
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Place a 'Spot Fire' in map."
                    ]
                }
              ]
            }, {
              name: 'Road Closure',
              icon: '/static/dist/static/symbols/fire/road_closure_point.svg',
              tints: self.tints,
              interactions: [self.annotations.pointDrawFactory()],
              style: self.annotations.getIconStyleFunction(self.tints),
              sketchStyle: self.annotations.getIconStyleFunction(self.tints),
              showName: true,
              selectedTint: 'selectedRoadClosurePoint',
              scope:["annotation"],
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Draw a 'Road Closure' on map ",
                        "Hold down the 'SHIFT' key during drawing to enable freehand mode. "
                    ]
                }
              ]
            }, {
              name: 'Control Line',
              icon: '/static/dist/static/symbols/fire/controlline.svg',
              interactions: [self.annotations.linestringDrawFactory()],
              size: 1,
              typeIcon: '/static/dist/static/symbols/fire/plus.svg',
              typeIconSelectedTint: 'selectedPlusIcon',
              typeIconDims: [20,20],
              colour: 'rgba(0, 0, 0, 0.1)',
              showName: true,
              scope:["annotation"],
              style: self.annotations.getVectorStyleFunc(this.tints),
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Draw a 'Control Line' on map ",
                        "Hold down the 'SHIFT' key during drawing to enable freehand mode. "
                    ]
                }
              ]
            },
            self.annotations.ui.defaultLine,
            self.annotations.ui.defaultPolygon,
            self.annotations.ui.defaultPoint
          ]
    
          sssTools.forEach(function (tool) {
            self.annotations.tools.push(tool)
          })
    
          self.loading.app.phaseEnd("initialize")
    
          // load map without layers
          self.loading.app.phaseBegin("init_olmap", 10, "Initialize olmap")
          self.map.init()
          self.loading.app.phaseEnd("init_olmap")
    
          self.loading.app.phaseBegin("load_catalogue", 20, "Load catalogue", true, true)
          try {
              self.catalogue.loadRemoteCatalogue( function () {
                //add default layers
                var failed_phase = null
                try {
                    self.loading.app.phaseEnd("load_catalogue")
    
                    self.loading.app.phaseBegin("init_map_layers", 10, "Initialize map layers")
                    failed_phase = "init_map_layers"
                    self.map.initLayers(self.fixedLayers, self.store.activeLayers)
                    self.loading.app.phaseEnd("init_map_layers")
    
                    // tell other components map is ready - wait for whoami to be
                    // populated first so components that gate on is_internal_dbca
                    // (e.g. the IWF weather forecast icon) are always visible when
                    // the user is entitled, regardless of network timing.
                    self.loading.app.phaseBegin("gk-init", 15, "Broadcast 'go-init' event")
                    failed_phase = "gk-init"
                    $.when(self._whoamiDeferred).always(function () {
                        try {
                        self.$broadcast('gk-init')
                        self.loading.app.phaseEnd("gk-init")

                        // after catalogue load trigger a tour
                        self.loading.app.phaseBegin("gk-postinit", 15, "Broadcast 'go-init' event")
                        failed_phase = "gk-postinit"
                        self.$broadcast('gk-postinit')
                        self.loading.app.phaseEnd("gk-postinit")

                        self.loading.app.phaseBegin("post_init", 10, "Post initialization")
                        failed_phase = "post-init"
                        self.store.layout.screenHeight = $(window).height()
                        self.store.layout.screenWidth = $(window).width()
                        $(window).resize(debounce(function(){
                            if ($(window).height() !== self.store.layout.screenHeight) {
                                self.store.layout.screenHeight = $(window).height()
                            }
                            if ($(window).width() !== self.store.layout.screenWidth) {
                                self.store.layout.screenWidth = $(window).width()
                            }
                        }, 200))
                        $("#menu-tab-layers-label").trigger("click")
                        self.store.activeMenu = "layers"
                        self.layers.setup()
                        $("#layers-active-label").trigger("click")
                        self.store.activeSubmenu = "active"
                        self.active.setup()

                        self.loading.app.phaseEnd("post_init")

                        if (self.store.settings.tourVersion !== tour.version) {
                          self.takeTour()
                        }
                        } catch(err) {
                            self.loading.app.phaseFailed(failed_phase, err)
                            throw err
                        }
                    })
                } catch(err) {
                    //some exception happens
                    self.loading.app.phaseFailed(failed_phase, err)
                    throw err
                }
              },function(reason){
                self.loading.app.phaseEnd("load_catalogue")
                alert(reason)
              })
          } catch(err) {
              //some exception happens
              self.loading.app.failed(err)
              throw err
          }
        }
      })
    })
}
