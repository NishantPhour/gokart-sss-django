<template>
  <div class="tabs-panel" id="menu-tab-bfrs">
    <div class="row collapse">
      <div class="columns">
        <ul class="tabs" id="bfrs-tabs">
          <li class="tabs-title is-active" >
            <a class="label" aria-selected="true" style="cursor:pointer;background-color:#ec5840;color:#fefefe" @click.stop.prevent="utils.editResource($event,null,env.bfrsService,env.bfrsService)">
                <span >Bushfire Reporting System</span>
                <small v-if="active.layerRefreshStatus(bushfireMapLayer)" style="white-space:pre-wrap"><br>Updated: {{ active.layerRefreshStatus(bushfireMapLayer) }}</small>
            </a>
          </li>
        </ul>
      </div>
    </div>

    <div class="row collapse" id="bfrs-tab-panels">
      <div class="columns">
        <div class="tabs-content vertical" data-tabs-content="bfrs-tabs">
          <div id="bfrs-list-tab" class="tabs-panel is-active" v-cloak>
            <div id="bfrs-list-controller-container">
                <div class="tool-slice row collapse">
                  <div class="small-12">
                    <div class="expanded button-group">
                      <a v-for="t in tools" class="button button-tool" v-bind:class="{'selected': t.name == annotations.tool.name}"
                        @click="annotations.setTool(t)" v-bind:title="t.label" style="font-size: 0.9rem;">{{{ annotations.icon(t) }}} {{t.showName?t.label:""}}</a>
                    </div>
                  </div>
                </div>
                <div class="row">
                  <div class="small-9 columns" >
                    <div class="row">
                      <div class="switch tiny">
                        <input class="switch-input" id="bushfiresInViewport" type="checkbox" v-bind:checked="viewportOnly" @change="toggleViewportOnly" />
                        <label class="switch-paddle" for="bushfiresInViewport">
                          <span class="show-for-sr">Viewport bushfires only</span>
                        </label>
                      </div>
                      <label for="bushfiresInViewport" class="side-label">Restrict to viewport ({{extentFeaturesSize}}/{{featureSize}})</label>
                    </div>
                  </div>
                  <div class="small-3 columns" style="text-align:right;padding-right:0px">
                    <span v-on:click="showToggles = !showToggles" style="cursor:pointer"><i class="fa {{showToggles?'fa-angle-double-up':'fa-angle-double-down'}}" aria-hidden="true"></i> Toggles</span>
                  </div>
                </div>
                <div v-show="showToggles">
                <div class="row">
                  <div class="switch tiny">
                    <input class="switch-input" id="toggleBushfireLabels" type="checkbox" v-bind:checked="bushfireLabels" @change="toggleBushfireLabels" v-bind:disabled="featureLabelDisabled" />
                    <label class="switch-paddle" for="toggleBushfireLabels">
                      <span class="show-for-sr">Display bushfire labels</span>
                    </label>
                  </div>
                  <label for="toggleBushfireLabels" class="side-label">Display bushfire labels</label>
                </div>
                <div class="row">
                  <div class="switch tiny">
                    <input class="switch-input" id="toggleReportInfo" type="checkbox" v-bind:disabled="!systemsetting.hoverInfoSwitchable" v-bind:checked="systemsetting.hoverInfo" @change="systemsetting.toggleHoverInfo" />
                    <label class="switch-paddle" for="toggleReportInfo">
                      <span class="show-for-sr">Display hovering bushfire info</span>
                    </label>
                  </div>
                  <label for="toggleReportInfo" class="side-label">Display hovering bushfire info</label>
                </div>
                <div class="row">
                  <div class="small-12">
                    <div class="columns">
                      <div class="row">
                        <div class="switch tiny">
                          <input class="switch-input" id="showFireboundary" type="checkbox" v-model="showFireboundary" />
                          <label class="switch-paddle" for="showFireboundary">
                            <span class="show-for-sr">Show fire boundary</span>
                         </label>
                        </div>
                        <label for="showFireboundary" style="side-label" class="side-label">Show fire boundary</label>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="row">
                  <div class="small-12">
                    <div class="columns">
                      <div class="row">
                        <div class="switch tiny">
                          <input class="switch-input" id="clippedBushfireReportOnly" v-bind:disabled="clippedFeatures.length === 0" type="checkbox" v-model="clippedOnly" @change="updateFeatureFilter(3,0)" />
                          <label class="switch-paddle" for="clippedBushfireReportOnly">
                            <span class="show-for-sr">Show saved selection</span>
                         </label>
                        </div>
                        <label for="clippedBushfireReportOnly" style="side-label" class="side-label">Show saved selection
                        </label>
                        <a class="button tiny secondary" title="Save selection" style="margin-top:0px;margin-bottom:5px;padding-top:6px;padding-left:1px;padding-right:1px;padding-bottom:0px;border:0px;height:24px;font-size:0.73rem;background-color:#2199e8" @click="clipToSelection()" v-bind:disabled="selectedFeaturesSize === 0">
                            Save selection ({{selectedFeaturesSize}})
                        </a>
                        ({{clippedFeatures.length}}/{{features.getLength()}})
                      </div>
                    </div>
                  </div>
                </div>

                </div>

                <div class="row collapse">
                  <div class="small-8 columns">
                    <input type="search" v-model="search" placeholder="Find a bushfire" @keyup="updateFeatureFilter(3)">
                  </div>
                  <div class="small-4 columns" style="text-align:right">
                    <span v-on:click="showFilters = !showFilters" style="cursor:pointer"><i class="fa {{showFilters?'fa-angle-double-up':'fa-angle-double-down'}}" aria-hidden="true"></i> Filters</span>
                  </div>
                </div>
                <div v-show="showFilters">
                <div class="row collapse">
                  <div class="small-6 columns">
                    <select name="select" v-model="region">
                      <option value="" selected>All regions</option>
                      <option v-for="r in regions"  value="{{r.region_id}}" track-by="region_id">
                        {{r.region}}
                      </option>
                    </select>
                  </div>
                  <div class="small-6 columns">
                    <select name="select" v-model="district" >
                      <option value="" selected>All districts</option>
                      <option v-for="d in districts"  value="{{d.id}}" track-by="id">
                        {{d.district}}
                      </option>
                    </select>
                  </div>
                </div>

                <div class="row collapse">
                  <div class="small-12 columns">
                    <p>Filtering uses created or fire detected date</p>
                  </div>
                </div>
                <div class="row collapse">
                  <div class="small-4">
                    <select name="select" v-model="dateRange" style="font-size:15px;">
                      <option value="">Date range</option>
                      <option value="21024">Last 24 hours </option>
                      <option value="31007">Last 7 days </option>
                      <option value="70001" selected>Current Financial Year </option>
                      <option value="-1">User Defined</option>
                    </select>
                  </div>
                  <div class="small-8">
                      <input type="text" id="bfrsStartDate" class="span2" v-model="startDate" placeholder="YYYY-MM-DD HH:mm" v-bind:disabled="dateRange !== '-1'" readonly></input>
                      <i class="fa fa-minus" style="margin-top:10px"></i>
                      <input type="text" id="bfrsEndDate" class="span2" v-model="endDate" placeholder="YYYY-MM-DD HH:mm"  v-bind:disabled="dateRange !== '-1'"  readonly></input>
                  </div>
                </div>

                <div class="row collapse">
                  <div class="small-6 columns">
                    <select name="select" v-model="statusFilter" >
                      <option value="all_reports" selected>All Reports</option>
                      <option value="initial_fire_report">Initial Fire Report</option>
                      <option value="notification_submitted">Notifications Submitted</option>
                      <option value="report_authorised">Report Authorised</option>
                      <option value="fire_not_found">Fire Not Found</option>
                    </select>
                  </div>
                  <div class="small-6 expanded button-group">
                    <a title="Search" class="button" style="height:38px;margin-left:10px;" @click="updateCQLFilter(0)">Search</a>
                    <a title="Reset filters" class="button" style="height:38px;margin-left:10px;" @click="resetFilters()">Reset</a>
                  </div>
                </div>

                </div>

                <div class="tool-slice row collapse">
                  <div class="small-12 expanded button-group">
                    <a title="Zoom to selected" class="button bfrsbutton" @click="zoomToSelected()" ><img style="width:13px;height:13px"src="/static/dist/static/images/zoom-to-selected.svg"/><br>Zoom To<br>Selected</a>
                    <a title="Refresh bushfire list" class="button bfrsbutton" @click="refreshBushfires()" ><i class="fa fa-refresh" aria-hidden="true"></i><br>Refresh<br>Bushfires </a>
                    <div v-show="canBatchUpload()" class="button bfrsbutton">
                        <label for="uploadBushfires" title="{{utils.importSpatialFileTypeDesc}}" >
                            <i class="fa fa-upload"></i><br>Batch<br>Upload
                        </label>
                        <input type="file" id="uploadBushfires" class="show-for-sr" name="bushfiresfile" accept="{{utils.importSpatialFileTypes}}" v-el:bushfiresfile @change="importList()"/>
                    </div>
                    <a v-show="canDownloadAll()" class="button bfrsbutton" @click="downloadList('gpkg','all')" title="Export Bushfire as GeoPackage"><i class="fa fa-download" aria-hidden="true"></i><br><span style='white-space:nowrap'>Download All</span><br>(gpkg) </a>
                    <a class="button bfrsbutton" @click="downloadList('gpkg','listed')" title="Export Bushfire as GeoPackage"><i class="fa fa-download" aria-hidden="true"></i><br>Download<br>(gpkg)</a>
                    <a class="button bfrsbutton" @click="downloadList('geojson','history')" title="Export Bushfire as GeoPackage"><i class="fa fa-download" aria-hidden="true"></i><br>Export<br>(geojson)</a>
                  </div>
                </div>

            </div>

            <div id="bfrs-list" class="layers-flexibleframe scroller" style="margin-left:-15px; margin-right:-15px;">
                            <div v-if="isFeatureListLoading" class="row">
                                <div class="small-12 columns" style="padding:12px 18px;">
                                    <div class="callout secondary" style="margin-bottom:8px;">
                                        <i class="fa fa-circle-o-notch fa-spin" aria-hidden="true"></i>
                                        Loading bushfires...
                                    </div>
                                </div>
                            </div>
              <template v-for="f in featurelist" track-by="get('id')">
                            <div v-if="!isFeatureListLoading && showFeature(f)" class="row feature-row" v-bind:class="{'feature-selected': isFeatureSelected(f) }" @click="toggleSelect(f)">
                <div class="small-12 columns">
                    <a v-if="canReset(f)"  @click.stop.prevent="resetFeature(f)" title="Reset" class="button tiny secondary float-right acion" style="margin-left:2px"><i class="fa fa-undo actionicon"></i></a>
                  <a v-if="canDelete(f)" @click.stop.prevent="deleteFeature(f)" title="Delete" class="button tiny secondary float-right action" style="margin-left:2px"><i class="fa fa-trash actionicon"></i></a>
                  <a v-if="canUpload(f)"  @click.stop.prevent="uploadBushfire(f)" title="Upload" class="button tiny secondary float-right acion" style="margin-left:2px"><i class="fa fa-upload actionicon"></i></a>
                  <a v-if="f.get('status') === 'in_queue'" @click.stop.prevent="showProgress(f)" title="Check Status" class="button tiny secondary float-right acion" style="margin-left:2px"><i class="fa fa-tasks"></i></a>
                  <a v-if="canModify(f)" @click.stop.prevent="startEditFeature(f)" title="Edit Bushfire" class="button tiny secondary float-right action">
                    <svg class="editicon"><use xlink:href="/static/dist/static/images/iD-sprite.svg#icon-area"></use></svg>
                  </a>
                  <a v-if="canCreate(f)" @click.stop.prevent="createFeature(f)" title="Create" class="button tiny secondary float-right action" style="margin-left:2px;background-color:red"><i class="fa fa-save actionicon"></i></a>
                  <a v-if="canEdit(f) " @click.stop.prevent="utils.editResource($event)" title="Open bushfire form" href="{{editUrl(f)}}" target="{{env.bfrsService}}" class="button tiny secondary float-right action" style="margin-left:2px"><i class="fa fa-pencil-square-o actionicon"></i></a>
                  <a v-if="canSave(f)" @click.stop.prevent="saveFeature(f)" title="Save" class="button tiny secondary float-right action" style="margin-left:2px;background-color:red">
                    <i class="fa fa-save actionicon"></i>
                  </a>
                  <div class="feature-title"><img class="feature-icon" id="bushfire-icon-{{f.get('id')}}" v-bind:src="featureIconSrc(f)" /> {{ f.get('fire_number') }} <i><small></small></i></div>
                </div>
                <div class="small-12 columns">
                      <div class="feature-title"><span class="reportname">{{f.get('name')}}</span></div>
                      <div v-if="f.get('status') === 'merged'" style="float:right"><img src="/static/dist/static/images/merge.svg"> {{f.get('linked_bushfire_number')}}</div>
                </div>
              </div>
              </template>
              <div class="small reveal" id="progressInfo" data-reveal data-close-on-click="false" >
            <h3>Status</h3>
            <div v-if="target_feature.get('status') === 'in_queue' && calculation_status === 'calculation_completed'" class="alert-container green-alert">
            <p style="font-size: 13px; margin: 0;">
                <i class="fa fa-info-circle"></i> Upload has been processed, please click ‘Complete’ Below to finalise the process
            </p>
            </div>
            <div v-if="target_feature.get('status') === 'in_queue' && target_feature.get('original_status') !== 'new' && calculation_status !== 'calculation_completed'" class="alert-container blue-alert">
            <p style="font-size: 13px; margin: 0;">
                <i class="fa fa-info-circle"></i> This window can be closed – you will receive an email when the upload is ready to proceed
            </p>
            </div>
            <table v-if="target_feature.get('status') === 'in_queue'" style=" width: 100%; font-size: 12px; margin-top: -5px; margin-bottom: 5px; border: none;">
                <tr>
                    <td style=" text-align: left; background-color: #EDEDED;"><b>Last Uploaded: </b>{{last_uploaded_date}}</td>
                    <td style=" text-align: left; background-color: #EDEDED;"><b>Submitted By: </b>{{submitter}}</td>
                    <td style="text-align: left; background-color: #EDEDED;">
                    <b>Status: </b>
                    <span v-if="calculation_status === 'waiting'" class="badge bg-primary">Waiting</span>
                    <span v-if="calculation_status === 'calculating'" class="badge bg-warning">Calculating</span>
                    <span v-if="calculation_status === 'calculation_error'" class="badge bg-danger">Failed</span>
                    <span v-if="calculation_status === 'calculation_completed'" class="badge bg-success">Completed</span>
                </td>
                </tr>
            </table>
            <div v-for="(index, task) in feature_tasks" :key="index">
                <div class="small-12 columns">
                <a class="task_status float-right" :title="revision && task.statusText">
                    <i :class="'fa ' + (revision && task.icon)"></i>
                </a>
                <a class="task_name">{{ task.description }}</a>
                </div>
                <div v-if="revision && task.message" class="small-12 columns">
                <p class="task_message">{{ task.message }}</p>
                </div>
            </div>
            <button class="close-button" data-close aria-label="Close modal" type="button">
                <span aria-hidden="true">&times;</span>
            </button>
            <div class="small-12 expanded button-group" style="justify-content: center;">
                <a title="Clear" class="button" style="flex: 0 0 auto; width: auto; margin: 0 4.165%; margin-top:10px" @click="clearQueue(withConfirm=true)" :disabled="clearButtonDisabled">Return to Edit Mode</a>
                <a title="Complete" class="button" style="flex: 0 0 auto; width: auto; margin: 0 4.165%; margin-top:10px" @click="captureMethods()" :disabled="completeButtonDisabled || !hasSpatialData">Complete</a>
            </div>
            </div>
            </div>
          </div>

        </div>
      </div>
    </div>

    <form id="bushfire_create" name="bushfire_create" action="{{createUrl()}}" method="post" target="{{utils.getWindowTarget(env.bfrsService)}}">
        <input type="hidden" name="sss_create" id="sss_create">
    </form>
  </div>
</template>
<style>
.reportname {
    font-style:italic;
    padding-left:24px;
    color:#6dd8ef;
    font-size:14px;
}

.button-group .bfrsbutton {
    padding-left:5px;
    padding-right:5px;
    font-size:0.8rem;
}
.actionicon {
    width:9px;
    height:9px;
}
.editicon {
    width:16px;
    height:16px;
    margin-top: -3px;
    margin-bottom: -4px;
    margin-left: -2px;
    margin-right: -2px;
}
.task_message {
    font-style:italic;
    font-weight:normal;
    color:red;
    font-size:12px;
    white-space:pre-wrap;
}
.task_name {
    font-style:normal;
    font-weight:bold;
    font-size:14px;
}
#bfrsStartDate,#bfrsEndDate {
    font-size:13px;
    width:118px;
    display:inline;
    cursor:pointer;
    padding-left:4px;
    padding-right:4px;
}
.alert-container {
    padding: 10px;
    margin-bottom: 20px;
    border: 1px solid #004085;
    border-radius: 6px;
    margin-top: -10px;
    position: relative;
    color: #004085;
}

.blue-alert {
    background-color: #cce5ff;
    border-color: #b8daff;
    color: #004085;
}

.green-alert {
    background-color: #d4edda;
    border-color: #c3e6cb;
    color: #155724;
}
.badge {
    display: inline-block;
    padding: 0.4em 0.8em;
    font-size: 85%;
    font-weight: 700;
    line-height: 1.1;
    text-align: center;
    white-space: nowrap;
    vertical-align: baseline;
    border-radius: 0.5rem;
}
.bg-primary {
    background-color: #2199E8;
    color: white;
}
.bg-warning {
    background-color: #ffc107;
    color: #212529;
}
.bg-danger {
    background-color: #dc3545;
    color: white;
}
.bg-success {
    background-color: #28a745;
    color: white;
}
</style>
<script>
    import { ol, $, Vue, moment, hash, turf, utils } from 'src/vendor.js'
  export default {
    store: {
        bushfireLabels: 'settings.bfrs.bushfireLabels',
        viewportOnly: 'settings.bfrs.viewportOnly',
        screenHeight: 'layout.screenHeight',
        hintsHeight: 'layout.hintsHeight',
        leftPanelHeadHeight: 'layout.leftPanelHeadHeight',
        activeMenu: 'activeMenu',
        hints: 'hints',
        whoami: 'whoami'
    },
    data: function () {
      var fill = '#ff6600'
      var stroke = '#7c3100'
      return {
        clippedOnly: false,
        search: '',
        statusFilter: "all_reports",
        target_feature: null,
        calculation_status: '',
        feature_tasks: [],
        region: '',
        district: '',
        last_uploaded_date: '',
        submitter: '',
        featureLabelDisabled: false,
        completeButtonDisabled: true,
        clearButtonDisabled: false,
        showFireboundary: false,
        tools: [],
        fields: ['fire_number', 'name'],
        calculation_result: null,
        progressRequestCount: 0,
        progressRequestPending: false,
        isFeatureListLoading: true,
        //sorted fields list (column,true?ascend:descend)
        sortedFields: [['fire_detected_or_created', false]],
        drawings: new ol.Collection(),
        features: new ol.Collection(),
        clippedFeatures: [],
        showFilters: false,
        taskDialog: null,
        showToggles: false,
        startDate: '',
        endDate: '',
        dateRange: '',
        revision: 1,
        selectRevision: 1,
        profileRevision: 1,
        extentFeaturesSize: 0,
        tints: {
          'new':[["#b43232","#c8c032"]],
          'new.textStroke':"#c8c032",
          'new.textFill':"#333",
          'new.fillColour':[0, 0, 0, 0.25],
          'new.colour':"#c8c032",
          'unknown': [['#b43232','#f90c25']],
          'unknown.textStroke': '#f90c25',
          'unknown.textFill': '#333',
          'unknown.fillColour':[0, 0, 0, 0.25],
          'unknown.colour': '#f90c25',
          'initial': [['#b43232','#999999']],
          'initial.textStroke': '#CCCCCC',
          'initial.textFill': '#333',
          'initial.fillColour':[0, 0, 0, 0.25],
          'initial.colour': '#D3D3D3',
          'draft_final': [['#b43232', '#FF0000']],
          'draft_final.textStroke': '#FF0000',
          'draft_final.textFill': '#FFFFFF',
          'draft_final.fillColour':[0, 0, 0, 0.25],
          'draft_final.colour': '#FF0000',
          'final_authorised': [['#b43232', '#00FF00']],
          'final_authorised.textStroke': '#00FF00',
          'final_authorised.textFill': '#333',
          'final_authorised.fillColour':[0, 0, 0, 0.25],
          'final_authorised.colour': '#00FF00',
          'reviewed': [['#b43232', '#00FF00']],
          'reviewed.textStroke': '#00FF00',
          'reviewed.textFill': '#333',
          'reviewed.fillColour':[0, 0, 0, 0.25],
          'reviewed.colour': '#00FF00',
          'modified':[["#b43232","#f57900"]],
          'modified.textStroke':"#f57900",
          'modified.textFill':"#333",
          'modified_authorised.fillColour':[0, 0, 0, 0.25],
          'modified.colour':"#f57900",
          'selected': [['#b43232', '#2199e8']],
          'selected.textStroke': '#2199e8',
          'selected.textFill': '#333',
        }
      }
    },
    computed: {
      map: function () { return this.$root.$refs.app.$refs.map },
      env: function () { return this.$root.env },
      annotations: function () { return this.$root.$refs.app.$refs.annotations },
      systemsetting: function () { return this.$root.systemsetting },
      dialog: function () { return this.$root.dialog },
      active: function () { return this.$root.active},
      measure: function () { return this.$root.measure },
      info: function () { return this.$root.info },
      catalogue: function () { return this.$root.catalogue },
      export: function () { return this.$root.export },
      loading: function () { return this.$root.loading },
      utils: function () { return this.$root.utils },
      moduleStatus: function(){
        return this._bfrsStatus || {}
      },
      isReportMapLayerHidden: function() {
        return this.$root.active.isHidden(this.bushfireMapLayer)
      },
      selectedFeatures: function () {
        return this.annotations.getSelectedFeatures("bfrs")
      },
      selectedFeaturesSize: function() {
        return this.selectRevision && this.selectedFeatures.getLength()
      },
      bushfireLayer: function() {
        return this.$root.catalogue.getLayer(this.env.bushfireListLayer)
      },
      bushfireMapLayer: function() {
        return this.$root.map?this.$root.map.getMapLayer(this.bushfireLayer):undefined
      },
      finalFireboundaryMapLayer: function() {
        return this.bushfireMapLayer?this.bushfireLayer.dependentLayers[0].mapLayer:null
      },
      selectedFinalFireboundaryMapLayer: function() {
        return this.bushfireMapLayer?this.bushfireLayer.dependentLayers[1].mapLayer:null
      },
      regions: function() {
        try{
            var regions = this.profileRevision && this.whoami["bushfire"]["regions"]
            return Array.isArray(regions)?regions:[]
        }catch(ex) {
            return []
        }
      },
      districts: function() {
        var vm = this
        var r = null
        if (this.region) {
            r = this.regions.find(function(o) { return o.region_id === parseInt(vm.region)})
        }
                return r && Array.isArray(r.districts)?r.districts:[]
      },
      bushfireStyleFunc: function() {

        if (!this._bushfireStyleFunc) {
            this._bushfireStyleFunc = function () {
                var vm = this
                var pointStyleFunc = vm.annotations.getIconStyleFunction(vm.tints)
                var boundaryStyleFunc = vm.annotations.getVectorStyleFunc(vm.tints)
                var labelStyleFunc = vm.annotations.getLabelStyleFunc(vm.tints, 'fire_number')
                return function(res) {
                    //var feat = this;
                    var feat = res;
                    
                    // console.log(res);
                    //console.log(new ol.Feature().getGeometry().getGeometriesArray())
                    if (typeof feat.getGeometry == "undefined") { 
                        return 
                    }
                    var geometries = feat.getGeometry().getGeometriesArray()
                    var pointStyle = (geometries.length > 0 || geometries[0] instanceof ol.geom.Point)?pointStyleFunc.call(feat, res):null
                    //show the fireboundary if showFireboudary is on or feat is selected
                    var boundaryStyle = ((vm.showFireboundary || feat.tint ) && (geometries.length > 1 || geometries[0] instanceof ol.geom.MultiPolygon))?boundaryStyleFunc.call(feat,res):null

                    var selfIntersectionStyle = null
                    if (boundaryStyle && feat.intersectionPoints) {
                        selfIntersectionStyle = new ol.style.Style({
                            geometry:feat.intersectionPoints,
                            image : new ol.style.Circle({
                                fill: new ol.style.Fill({
                                    color: [255,0,0],
                                }),
                                radius:4
                            })
                        })
                    }

                    var labelStyle = null
                    if (vm.map.olmap.getView().getResolution() < 0.003 && geometries.length > 0 && feat.get('fire_number') && vm.bushfireLabels && !vm.$root.active.isHidden(vm.map.getMapLayer(vm.env.bushfireListLayer))) {
                      labelStyle = labelStyleFunc.call(feat, res)
                      labelStyle.setGeometry(geometries[0])
                    }

                    var style = null
                    if ((pointStyle && 1) + (boundaryStyle && 1) + (labelStyle && 1)  + (selfIntersectionStyle && 1) === 1) {
                        return pointStyle || boundaryStyle || labelStyle || selfIntersectionStyle
                    } else {
                        if (!vm._bushfireStyle) {
                            vm._bushfireStyle = []
                        } else {
                            vm._bushfireStyle.length = 0
                        }
                        if (pointStyle) {vm._bushfireStyle.push.apply(vm._bushfireStyle, pointStyle)}
                        if (boundaryStyle) {vm._bushfireStyle.push.apply(vm._bushfireStyle, boundaryStyle)}
                        if (labelStyle) {vm._bushfireStyle.push(labelStyle)}
                        if (selfIntersectionStyle) {vm._bushfireStyle.push(selfIntersectionStyle)}
                        return vm._bushfireStyle
                    }
                }
            }.call(this)
        }
        return this._bushfireStyleFunc
      },
      featurelist: function() {
        try {
            return this.revision && this._featurelist.getArray()
        } catch (ex) {
            return [];
        }
      },
      featureSize:function() {
        try {
            return this.revision && this._featurelist.getLength()
        } catch (ex) {
            return 0;
        }
      },
      hasFeatureFilter: function () {
        return (this.search && this.search.trim())?true:false
            },
            hasSpatialData: function () {
                return !!(this.target_feature && this.target_feature.spatial_data)
      }
    },
    watch: {
            hasSpatialData:function(hasSpatialData) {
                if (!hasSpatialData && this.calculation_status === 'calculation_completed' &&
                        this.target_feature && this.target_feature.get('status') === 'in_queue' &&
                        this.taskDialog && this.taskDialog.isActive) {
                    this.completeButtonDisabled = true
                    this.updateBfrsUploadProgress()
                }
            },
      isReportMapLayerHidden:function(newValue,oldValue) {
        if (newValue === undefined || oldValue === undefined) {
            //layer is turned on or turned off
            return
        } else if (this.map.resolution >= 0.003) {
            //label is turned on, but resolution is not less than 0.003
            return
        } else {
            //label is enabled, hiding/showing bfrs layer requires resetting the style text.
            this.bushfireMapLayer.changed()
        }
      },
      bushfireLabels:function(newValue,oldValue) {
        this.showBushfireLabels()
      },
      tools:function(newValue,oldValue) {
        this.adjustHeight()
      },
      showFilters:function(newValue,oldValue) {
        this.adjustHeight()
      },
      showToggles:function(newValue,oldValue) {
        this.adjustHeight()
      },
      showFireboundary:function(newValue,oldValue) {
        var vm = this
        this.map.enableDependentLayer(this.bushfireMapLayer,this.env.bushfireFinalFireBoundaryLatestLayer,newValue)
        $.each(this._featurelist.getArray(),function(index,feature){
            if (vm.isFireboundaryDrawable(feature)) {
                feature.getGeometry().changed()
            }
        })
      },
      clippedFeatures:function(newValue,oldValue) {
        if (!this.clippedOnly) return
        if (newValue.length === 0) {
            this.clippedOnly = false
            this.updateFeatureFilter(3,0)
        }
      },
      dateRange: function(newValue,oldValue) {
        this.changeDateRange()
      },
      startDate: function(newValue,oldValue) {
        this.changeStartDate()
      },
      endDate: function(newValue,oldValue) {
        this.changeEndDate()
      },
      region: function(newValue,oldValue) {
        this.district = ""
      }
    },
    methods: {
      regionFilter: function(downloadFilter) {
        if (downloadFilter) {
            var vm = this
            var r = this.regions.find(function(o){return o.region_id === parseInt(vm.region)})
            return this.region?("region='" + (r?r.region:"") + "'") : null
        } else {
            return this.region?("region_id=" + this.region) : null
        }
      },
      changeDateRange: function() {
        if (this.dateRange === "-1") {
            //customized
            this.changeStartDate()
            this.changeEndDate()
        } else if (this.dateRange === "") {
            this.endDate = ''
            this.startDate = ''
        } else {
            var range = utils.getDateRange(this.dateRange,"YYYY-MM-DD HH:mm")
            this.startDate = range[0] || ""
            this.endDate = range[1] || ""
        }
      },
      changeStartDate: function() {
        if (this.dateRange !== "-1") {
            //not in editing mode
            return
        }
        if (!this._endDatePicker) return
        try {
            if (this.startDate === "") {
                this._endDatePicker.setStartDate(moment().format("YYYY-MM-DD") + " 00:00")
            } else {
                this._endDatePicker.setStartDate(moment(this.startDate,"YYYY-MM-DD HH:mm").format("YYYY-MM-DD") + " 00:00")
            }
        } catch(ex) {
        }
      },
      changeEndDate: function() {
        if (this.dateRange !== "-1") {
            //not in editing mode
            return
        }
        if (!this._startDatePicker) return
        try {
            if (this.endDate === "") {
                this._startDatePicker.setEndDate(moment().format("YYYY-MM-DD") + " 23:59")
            } else {
                this._startDatePicker.setEndDate(this.endDate)
            }
        } catch(ex) {
        }
      },
      dateFilter: function() {

        if (this.dateRange === "70001") {
            var now = moment.utc()

            var fyYear = (now.month() >= 6) ? now.year() : now.year() - 1
            var fyStart = moment.utc(`${fyYear}-07-01T00:00:00Z`)

            return "fire_detected_or_created >= '" + fyStart.format("YYYY-MM-DDTHH:mm:ssZ") + "'"
        }

        if (this.dateRange !== "-1") {
            //in predefined range, reset the startDate and endDate
            this.changeDateRange()
        }

        var startDate = (this.startDate) ? moment(this.startDate,"YYYY-MM-DD HH:mm",true) : null
        if (startDate && !startDate.isValid()) {
            throw "startDate is under changing."
        }

        var endDate = (this.endDate && this.endDate < moment().format("YYYY-MM-DD HH:mm"))
            ? moment(this.endDate,"YYYY-MM-DD HH:mm",true)
            : null

        if (endDate && !endDate.isValid()) {
            throw "endDate is under changing."
        }

        if (startDate) {
            if (endDate) {
                if (startDate >= endDate) {
                    throw "Start date must be less than end date."
                }
                return "fire_detected_or_created BETWEEN '" 
                    + startDate.utc().format("YYYY-MM-DDTHH:mm:ssZ") 
                    + "' AND '" 
                    + utils.nextDate(endDate,"YYYY-MM-DD HH:mm").utc().format("YYYY-MM-DDTHH:mm:ssZ") 
                    + "'"
            } else {
                return "fire_detected_or_created >= '" 
                    + startDate.utc().format("YYYY-MM-DDTHH:mm:ssZ") 
                    + "'"
            }
        } else if (endDate) {
            return "fire_detected_or_created < '" 
                + utils.nextDate(endDate,"YYYY-MM-DD HH:mm").utc().format("YYYY-MM-DDTHH:mm:ssZ") 
                + "'"
        }

        var now = moment.utc()
        var fyYear = (now.month() >= 6) ? now.year() : now.year() - 1
        var fyStart = moment.utc(`${fyYear}-07-01T00:00:00Z`)

        return "fire_detected_or_created >= '" + fyStart.format("YYYY-MM-DDTHH:mm:ssZ") + "'"
    },
      districtFilter: function(downloadFilter) {
        if (downloadFilter) {
            var vm = this
            var d = this.districts.find(function(o){return o.id === parseInt(vm.district)})
            return this.district?("district='" + (d?d.district:"") + "'") : null
        } else {
            return this.district?("district_id=" + this.district) : null
        }
      },
      originpointCoordinate: function(feat){
        try {
            return feat.getGeometry().getGeometriesArray()[0].getCoordinates()
        } catch (ex) {
            return null
        }
      },
      featureTasks: function(feat) {
        return this.revision && ((this._taskManager)?this._taskManager.getTasks(feat):null)
      },
      refreshFinalFireboundaryLayer: function(wait) {
        var vm = this
        wait = wait || 1000
        this._refreshFinalFireboundaryLayer = this._refreshFinalFireboundaryLayer || debounce(function(){
            if (vm.finalFireboundaryMapLayer && vm.finalFireboundaryMapLayer.show) {
                vm.finalFireboundaryMapLayer.refresh()
            }
        },wait)

        this._refreshFinalFireboundaryLayer.call({wait:wait})
      },
      refreshSelectedFinalFireboundaryLayer: function(wait) {
        var vm = this
        wait = wait || 1000
        this._refreshSelectedFinalFireboundaryLayer = this._refreshSelectedFinalFireboundaryLayer || debounce(function(){
          if (!vm.selectedFinalFireboundaryMapLayer) return

          var selectedFinalBushfires = vm.selectedFeatures.getArray().filter(function(f) {return !vm.isFireboundaryDrawable(f)})
          if (selectedFinalBushfires.length === 0) {
            if (vm.selectedFinalFireboundaryMapLayer.show) {
                vm.map.enableDependentLayer(vm.bushfireMapLayer,vm.env.bushfireFinalFireBoundaryLatestLayer + "_selected",false)
            }
          } else {
            vm.selectedFinalFireboundaryMapLayer.setParams({
                cql_filter:"fire_number in ('" + selectedFinalBushfires.map(function(f){return f.get('fire_number')}).join("','") +  "')"
            })
            if (!vm.selectedFinalFireboundaryMapLayer.show) {
                vm.map.enableDependentLayer(vm.bushfireMapLayer,vm.env.bushfireFinalFireBoundaryLatestLayer + "_selected",true)
            }
          }
        },wait)

        this._refreshSelectedFinalFireboundaryLayer.call({wait:wait})
      },
      featureExtent: function(feat) {
        if (feat.get('fire_boundary')) {
            if (feat.getGeometry()) {
                return ol.extent.extend(feat.getGeometry().getExtent(),feat.get('fire_boundary'))
            } else {
                return feat.get('fire_boundary')
            }
        } else {
            return feat.getGeometry().getExtent()
        }
      },
      zoomToSelected: function(wait) {
        var vm = this
        wait = wait || 0
        vm._zoomToSelected = vm._zoomToSelectedFunc || debounce(function() {
            vm.map.zoomToSelected(125,vm.featureExtent)
        },wait)
        if (wait === 0) {
            vm._zoomToSelected.call({wait:1})
        } else {
            vm._zoomToSelected.call({wait:wait})
        }
      },
      open: function(options) {
		// PWM: can't find anywhere this is used
        //active bfrs module
        if (this.activeMenu !== "bfrs") {
            $("#menu-tab-bfrs-label").trigger("click")
        } else if(!$('#offCanvasLeft').hasClass('reveal-responsive')){
            $('#offCanvasLeft').toggleClass('reveal-responsive')
            self.map.olmap.updateSize()
        }

        var vm = this
        var updateType = null
        var action = options["action"] || "select"
        if (!options) {return}
        if ("region" in options) {
            if (this.region !== "" && options["region"] !== this.region) {
                this.region = options["region"] || ""
                updateType = "region"
            }
        }
        if ("district" in options) {
            if (this.district !== "" && options["district"] !== this.district) {
                this.district = options["district"] || ""
                updateType = "district"
            }
        }
        if (options["bushfireid"] !== null && options["bushfireid"] !== undefined){
            if (this.selectedFeatures.getLength() > 0) {
                this.selectedFeatures.clear()
            }
            if (this.search && this.search.trim().length > 0) {
                if (this.clippedOnly) this.clippedOnly = false
                this.search = ""
                this.updateFeatureFilter(3,0)
            } else if (this.clippedOnly) {
                this.clippedOnly = false
                this.updateFeatureFilter(1,0)
            }
        }

        updateType = updateType || ((action === "create")?"query":null)
        if (!updateType && options["bushfireid"] !== null && options["bushfireid"] !== undefined){
            var bushfire = this.features.getArray().find(function(f) {return f.get('fire_number') === options["bushfireid"]})
            if (bushfire) {
                this.selectedFeatures.push(bushfire)
                if (options["refresh"] || action === "update") {
                    this.resetFeature(bushfire,false,function() {
                        vm.zoomToSelected()
                        vm.scrollToSelected()
                    })
                } else {
                    this.zoomToSelected()
                    this.scrollToSelected()
                }
                return
            } else {
                updateType = "query"
            }
        }

        if (updateType || options["refresh"]) {
            if (options["bushfireid"] !== null && options["bushfireid"] !== undefined){
                //want to find some bushfire, clear other filters
                if (this.statusFilter !== "all_reports") {
                    this.statusFilter = "all_reports"
                }
                if (this.dateRange !== "") {
                    this.dateRange = ""
                    this.startDate = ""
                    this.endDate = ""
                }
            }
            updateType = options["refresh"]?"refresh":updateType
            this.updateCQLFilter(1, true, function(){
                if (options["bushfireid"] !== null && options["bushfireid"] !== undefined){
                    var feat = vm.features.getArray().find(function(o) {return o.get('fire_number') == options["bushfireid"]})
                    if (feat) {
                        vm.selectedFeatures.push(feat)
                        vm.zoomToSelected()
                        vm.scrollToSelected()
                    }
                }

            })
        }

      },
      isModifiable: function(bushfire) {
        try{
            return this.whoami["bushfire"]["permission"][bushfire.get('status') + ".modify"]
        } catch(ex){
            return false
        }
      },
      isFireboundaryDrawable: function(bushfire) {
        return bushfire.get('status') === "new" || (bushfire.get('report_status') === 1) || (bushfire.get('report_status') === 2) || (bushfire.get('report_status') === 3)
      },
      isEditable: function(bushfire) {
        try{
            return this.whoami["bushfire"]["permission"][bushfire.get('status') + ".edit"]
        } catch(ex){
            return false
        }
      },
      isDeletable: function(bushfire) {
        return bushfire.get('status') === "new"
      },
      isCreatable: function() {
        try {
            return this.revision && this.whoami["bushfire"]["permission"]["create"]
        } catch(ex) {
            return false
        }
      },
      canBatchUpload: function() {
        try{
            return this.revision && this.whoami["bushfire"]["permission"]["final_authorised.modify"]
        } catch(ex) {
            return false
        }
      },
      canDownloadAll: function() {
        return true
        /*
        try{
            return this.revision && this.whoami["bushfire"]["permission"]["final_authorised.modify"]
        } catch(ex) {
            return false
        }
        */
      },
      canEdit: function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" && this.isEditable(bushfire) && bushfire.get('tint') !== "modified"
      },
      canUpload: function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" && this.isModifiable(bushfire)
      },
      canModify: function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" && this.isFireboundaryDrawable(bushfire) && this.isModifiable(bushfire)
      },
      canReset: function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" // && this.isEditable(bushfire) && bushfire.get('tint') === "modified"
      },
      canSave: function(bushfire) {
        return this.revision && bushfire.get('status') !== "new" && this.isModifiable(bushfire) && bushfire.get('tint') === "modified"
      },
      canCreate: function(bushfire) {
        return this.revision && bushfire.get('status') === "new" && bushfire.getGeometry().getGeometriesArray().find(function(g) {return g instanceof ol.geom.Point})
      },
      canDelete: function(bushfire) {
        return this.revision && this.isDeletable(bushfire)
      },
      createUrl: function() {
        return this.env.bfrsService + "/bfrs/create/"
      },
      editUrl: function(feat) {
        var status = feat.get('report_status')
        if (status > 1 && status < 5) {
            return this.env.bfrsService + "/bfrs/final/" + feat.get('id') + "/"
        } else {
            return this.env.bfrsService + "/bfrs/initial/" + feat.get('id') + "/"
        }
      },
      saveUrl: function(feat) {
        return this.env.bfrsService + "/api/v1/bushfirespatial/" + feat.get('id') + "/?format=json"
      },
      deleteUrl: function(feat) {
        return this.env.bfrsService + "/delete/" + feat.get('id')
      },
      startEditFeature: function(feat) {
        if (this.selectedFeatures.getLength() !== 1 || this.selectedFeatures.item(0) !== feat) {
            if (this.selectedFeatures.getLength() > 0) this.selectedFeatures.clear()
            this.selectedFeatures.push(feat)
        }
        if (this.annotations.tool !== this.ui.modifyTool) {
            this.annotations.setTool(this.ui.modifyTool)
        }
      },
      validateBushfire: function(feat, validateType, callback) {
        if (feat.intersectionPoints) {
            delete feat.intersectionPoints
            feat.changed()
        }

        var indexes = null
        this._validateBushfireCallback = this._validateBushfireCallback || function(error, callback) {
            if (callback) {
                callback(error)
            } else if (error) {
                alert(error)
            }
        }
        var vm = this
        try {
            var geometries = feat.getGeometry().getGeometries()
            var originPoint = geometries.find(function(g) {return g instanceof ol.geom.Point}) || null

            if (!originPoint) {
                throw "No origin point placed"
            }
            if (!this.isFireboundaryDrawable(feat)) {
                if ((feat.get('modifyType') & 2) !== 2) {
                    if (feat.get('fire_boundary')) {
                        //only move  the original point
                        originPoint = originPoint.getCoordinates()
                        if (validateType === "getSpatialData") {
                            //during saving, check agaist the fire boundary
                            const layer_id = getLayerId(vm.env.bushfireFinalFireBoundaryLatestLayer);
                            url = getLayerUrl(layer_id, vm.env);
                            $.ajax({
                                url:url + "/wfs?service=wfs&version=2.0&request=GetPropertyValue&valueReference=fire_number&typeNames=" + getLayerId(vm.env.bushfireFinalFireBoundaryLatestLayer) + "&cql_filter=(fire_number='" + feat.get('fire_number') + "')and (CONTAINS(fire_boundary,POINT(" + originPoint[1]  + " " + originPoint[0] + ")))",
                                dataType:"xml",
                                success: function (response, stat, xhr) {
                                    if (response.firstChild && response.firstChild.children && response.firstChild.children.length > 0) {
                                        vm._validateBushfireCallback(null,callback)
                                    } else if (callback) {
                                        vm._validateBushfireCallback("Point of Origin is not inside fire boundary, please fix using the edit bushfire button",callback)
                                    }
                                },
                                error: function (xhr, status, message) {
                                    vm._validateBushfireCallback(xhr.responseText || message,callback)
                                },
                                xhrFields: {
                                    withCredentials: true
                                }
                            })
                        } else {
                            //during modifing,check agaist the bbox of fire boundary
                            if (ol.extent.containsCoordinate(feat.get('fire_boundary'), originPoint)) {
                                vm._validateBushfireCallback(null, callback)
                            } else {
                                vm._validateBushfireCallback("Point of Origin is not inside fire boundary, please fix using the edit bushfire button",callback)
                            }
                        }
                    } else {
                        vm._validateBushfireCallback(null,callback)
                    }
                } else {
                    vm._validateBushfireCallback(null,callback)
                }
                return
            }

            var fireboundary = null
            indexes = geometries.findIndex(function(g) {return g instanceof ol.geom.MultiPolygon})
            if (indexes >= 0) {
                fireboundary = geometries[indexes]
                indexes = [indexes]
            } else {
                fireboundary = null
                indexes = null
            }

            var polygon = null
            var polygonIndex = -1
            var convertedToTurf = true
            var checkResult = false
            //check self-intersect and polygon intersect.
            //during checking, polygons are converted into turf polygon and cached in the local variable
            if (fireboundary && fireboundary.getPolygons().length === 1) {
                fireboundary = fireboundary.getCoordinates()
                fireboundary[0] = turf.polygon(fireboundary[0])
                var kinks = turf.kinks(fireboundary[0])
                if (kinks.features.length > 0) {
                    feat.intersectionPoints = new ol.geom.MultiPoint(kinks.features.map(function(p) {return p.geometry.coordinates}))
                    if (indexes) indexes.push(0)
                    throw "The polygon is self intersecting, please remove intersection"
                }
            } else if (fireboundary && fireboundary.getPolygons().length > 1) {
                fireboundary = fireboundary.getCoordinates()
                //validate whether any existed polygons are intersect
                for(index = 0;index < fireboundary.length;index++) {
                    if (index === 0) {fireboundary[index] = turf.polygon(fireboundary[index])}
                    for(index2 = index + 1;index2 < fireboundary.length;index2++) {
                        if (index === 0) {fireboundary[index2] = turf.polygon(fireboundary[index2])}
                        try {
                            checkResult = turf.intersect(fireboundary[index],fireboundary[index2])
                        } catch(ex) {
                            var kinks = null
                            if (index === 0 && index2 === 1 && (kinks = turf.kinks(fireboundary[index])).features.length > 0) {
                                feat.intersectionPoints = new ol.geom.MultiPoint(kinks.features.map(function(p) {return p.geometry.coordinates}))
                                if (indexes) indexes.push(index)
                                throw "One or more fire boundaries are self intersecting, please remove self intersection"
                            } else if (index === 0 && (kinks = turf.kinks(fireboundary[index2])).features.length > 0) {
                                feat.intersectionPoints = new ol.geom.MultiPoint(kinks.features.map(function(p) {return p.geometry.coordinates}))
                                if (indexes) indexes.push(index2)
                                throw "One or more fire boundaries are self intersecting, please remove self intersection"
                            } else {
                                if (indexes) indexes.push(index)
                                throw "One or more fire boundaries are invalid, please fix it"
                            }
                        }
                        if (checkResult) {
                            if (indexes) indexes.push(index)
                            throw "One or more fire boundaries are intersecting, please remove intersection"
                        }
                    }
                }
            }

            if (originPoint) {
                inFireboundary = null
                originPoint = turf.point(originPoint.getCoordinates())
                //checking whether origin point is in a existing fireboundary
                if (fireboundary && fireboundary.length > 0) {
                    inFireboundary = false
                    for(index = 0;index < fireboundary.length;index++) {
                        if (!convertedToTurf) {
                            fireboundary[index] = turf.polygon(fireboundary[index])
                        }
                        if (turf.inside(originPoint,fireboundary[index])) {
                            inFireboundary = true
                            break;
                        }
                    }
                }
                //checking whether origin point is in new fireboundary
                if (inFireboundary !== true && polygon && validateType !== "deleteFireboundary" && polygonIndex === -1) {
                    inFireboundary = false
                    if (turf.inside(originPoint,polygon)) {
                        inFireboundary = true
                    }
                }

                if (inFireboundary === false) {
                    indexes = [0]
                    throw "Point of Origin is not inside fire boundary, please fix using the edit bushfire button"
                }
                convertedToTurf = true
            }
            vm._validateBushfireCallback(null,callback)
        }catch(ex) {
            if (!feat.get('external_feature')) {
                if (indexes) {feat['selectedIndex'] = indexes}
                if (this.annotations.selectedFeatures.getLength() !== 1 || this.annotations.selectedFeatures.item(0) !== feat) {
                    this.annotations.selectedFeatures.clear()
                    this.annotations.selectedFeatures.push(feat)
                }
                if (this.annotations.tool !== this.ui.modifyTool) {
                    this.annotations.setTool(this.ui.modifyTool)
                }
            }

            vm._validateBushfireCallback(ex.message || ex,callback)
        }
      },
      getSpatialData: function(feat,caller,callback,failedCallback) {
        caller = caller || "get"
        var vm = this
        this._defaultFailedCallback = this._defaultFailedCallback || function(msg) {
            alert(msg)
        }
        failedCallback = failedCallback || this._defaultFailedCallback
        vm._getSpatialDataCallback = vm._getSpatialDataCallback || function(feat,caller,callback,failedCallback,spatialData) {
            if (spatialData && vm.target_feature && (caller === 'import' || caller === 'save' || caller === 'create')) {
                Vue.set(vm.target_feature, 'spatial_data', spatialData);
            }
            if(vm.target_feature.spatial_data){
                spatialData = vm.target_feature.spatial_data
            }
            if(vm.target_feature && vm.target_feature.get("fire_number")){
                if(feat.get("fire_number")){
                    if(vm.target_feature.get("fire_number") === feat.get("fire_number")){
                        feat.tasks = vm.target_feature.tasks
                    }
                }
            }
            if (vm._taskManager.allTasksSucceed(feat,"getSpatialData")) {
                if(!spatialData){ //in case spatial_data is lost, reload the spatial data from the backend again
                    vm.completeButtonDisabled = true
                    vm.showProgress(vm.target_feature, 'updateBfrsUploadProgress')
                    return
                }
                if ("region" in spatialData && "district" in spatialData) {
                    var region = null
                    var district = null
                    spatialData["region_id"] = null
                    spatialData["district_id"] = null

                    var name = spatialData["region"]
                    delete spatialData["region"]
                    if (name) {
                        name = name.toLowerCase()
                        region = vm.regions.find(function(o) {return o.region.toLowerCase() === name})
                        if (region) {
                            spatialData["region_id"] = region.region_id
                        } else {
                            failedCallback("Region '" + name + "' is not found")
                            return
                        }
                    }

                    name = spatialData["district"]
                    delete spatialData["district"]
                    if (name && region) {
                        name = name.toLowerCase()
                        district = region.districts.find(function(o) {return o.district.toLowerCase() === name})
                        if (district) {
                            spatialData["district_id"] = district.id
                        } else {
                            failedCallback("District '" + name + "' is not found in region '" + region.region + "'.")
                            return
                        }
                    }
                }


                if (caller === "batchimport" && spatialData["fire_boundary"]) {
                    //try to set capture method if have
                    if (feat.get("capt_meth")) {
                        method = vm.whoami["bushfire"]["capturemethods"].find(function(m) { return m.code === feat.get("capt_meth")})
                        if (method) {
                            //found the capture method in the list
                            spatialData["capturemethod"] = method.id
                        } else if (feat.get("capt_desc")) {
                            //can't find the capture method in the list, and have non empty capture method description, use 'other'
                            spatialData["capturemethod"] = vm.whoami["bushfire"]["other_capturemethod_id"]
                        }
                        if (spatialData["capturemethod"] === vm.whoami["bushfire"]["other_capturemethod_id"]) {
                            //is other capture method
                            spatialData["other_capturemethod"] = feat.get("capt_desc")
                        }
                    }
                    callback(spatialData)
                }
                else if (caller === "showprogress" && spatialData["fire_boundary"]) {
                    if(feat.get('original_status') === 'new'){
                        callback(spatialData)
                    }
                    else{
                        Vue.set(vm.target_feature, 'spatial_data', spatialData)
                    }     
                }
                else if (caller === "save" && spatialData["fire_boundary"]) {
                    Vue.set(vm.target_feature, 'spatial_data', spatialData)
                }
                else if (caller === "capturemethod" && vm.target_feature.spatial_data && vm.target_feature.spatial_data["fire_boundary"]) {
                    var spatialData = vm.target_feature.spatial_data
                    vm.loadCapturemethods(function(){
                        initData = {}
                        if (feat.get("capt_meth")) {
                            method = vm.whoami["bushfire"]["capturemethods"].find(function(m) { return m.code === feat.get("capt_meth")})
                            if (method) {
                                initData["capturemethod"] = method.id
                            }
                        }
                        if (feat.get("capt_desc")) {
                            initData["other_capturemethod"] = feat.get("capt_desc")
                        }
                        vm.taskDialog.close()
                        vm.dialog.show({
                            "title":"Capture Methods",
                            "messages":vm.whoami["bushfire"]["capturemethod_dialogmessage"],
                            "initData": initData,
                            "initFunc": function() {
                                if ("capturemethod" in initData) {
                                    $("#userdialog-button-true").prop("disabled",false);
                                }
                                if (initData["capturemethod"] === vm.whoami["bushfire"]["other_capturemethod_id"]) {
                                    $("#userdialog input[name='other_capturemethod']").prop("disabled",false)
                                }
                            },
                            "footer":[[
                                ["",3],
                                [true,2,{
                                    type:"button",
                                    disabled:true,
                                    title:"Select",
                                    click:"close",
                                    is_valid:function(button,data){
                                        if (!data["capturemethod"]) {
                                            alert("Please choose a capture method.")
                                            return false

                                        } else if (parseInt(data["capturemethod"]) === vm.whoami["bushfire"]["othermethod_id"] && (!data["other_capturemethod"])) {
                                            alert("Please input the other capture method.")
                                            return false
                                        }
                                    }
                                }],
                                ["",2],
                                [false,2,{
                                    type:"button",
                                    disabled:false,
                                    click:"close",
                                    title:"Cancel"
                                    }
                                ],
                                ["",3]
                            ]],
                            "defaultOption":false,
                            "callback":function(isOk,data) {
                                if (isOk) {
                                    if (!data["capturemethod"]) {
                                        failedCallback("'Capture Method' is missing.")
                                    } else if (data["capturemethod"] === vm.whoami["bushfire"]["othermethod_id"] && (!data["other_capturemethod"])) {
                                        failedCallback("'Other Capture Method' is missing.")
                                    } else {
                                        spatialData["capturemethod"] = data["capturemethod"]
                                        if (data["capturemethod"] === vm.whoami["bushfire"]["othermethod_id"]) {
                                            spatialData["other_capturemethod"] = data["other_capturemethod"] || null
                                        }
                                        callback(spatialData)
                                    }

                                } else {
                                    failedCallback("Import cancelled")
                                }
                            }
                        })
                    },
                    function(msg){
                        failedCallback(msg)
                    })
                } else {
                    callback(spatialData)
                }

            } else if (vm._taskManager.allTasksFinished(feat,"getSpatialData")) {
                if (failedCallback === vm._defaultFailedCallback) {
                    var msg = vm._taskManager.errorMessages(feat,"getSpatialData").join("\r\n")
                    if (msg) alert(msg)
                } else {
                    failedCallback("")
                }
            }
        }

        vm._getSpatialData = vm._getSpatialData || function(feat,caller,callback,failedCallback) {
            try{
                if(caller === "capturemethod"){
                    vm._getSpatialDataCallback(feat,caller,callback,failedCallback,vm.target_feature.spatial_data)
                    return
                }
                
                var spatialData = {}
                var modifyType = (feat.get('status') === 'new')?3:(feat.get('modifyType') || 3)

                if(caller === 'showprogress'){
                    modifyType = (feat.get('status') === 'new')?3:(feat.get('modifyType') || 2)
                }

                var geometries = feat.getGeometry().getGeometriesArray()
                var originPoint = geometries.find(function(g){return g instanceof ol.geom.Point}) || null
                originPoint = originPoint?originPoint.getCoordinates():null

                var fireboundary = null
                var bbox = null
                var area = 0
                if ((modifyType & 1) === 1) {
                    spatialData["origin_point"] = originPoint
                    spatialData["origin_point_mga"] = vm.map.getMGA(originPoint)
                    spatialData["tenure_ignition_point"]  = null
                    spatialData["fire_position"]  = null
                }

                if ((modifyType & 2) === 2) {
                    fireboundary = geometries.find(function(g) {return g instanceof ol.geom.MultiPolygon}) || null
                    bbox = (fireboundary && fireboundary.getPolygons().length > 0)?fireboundary.getExtent():null
                    fireboundary = (fireboundary && fireboundary.getPolygons().length > 0)?fireboundary.getCoordinates():null

                    spatialData["fire_boundary"] = fireboundary
                    spatialData["area"] = null
                }

                // Area breakdown should still run when only origin point was modified,
                // as long as the feature already has a fire boundary geometry.
                if (!fireboundary) {
                    var existingFireboundary = geometries.find(function(g) {return g instanceof ol.geom.MultiPolygon}) || null
                    fireboundary = (existingFireboundary && existingFireboundary.getPolygons().length > 0)
                        ? existingFireboundary.getCoordinates()
                        : null
                }

                var tenure_area_task = null
                var tasks = vm.featureTasks(vm.target_feature);
                /*
                 * if grey bushfires not required to have area breakdown use this code.:
                 * if (fireboundary && (modifyType & 2) === 2 && caller !== 'showprogress') {
                 *     spatialData["area"] = null
                 *     var tenure_area_task = tasks.find(task => task.taskId === 'tenure_area');
                 *     if (!tenure_area_task){
                 *         var tenure_area_task = vm._taskManager.addTask(feat,"getSpatialData","tenure_area","Calculate fire boundary areas",utils.WAITING)
                 *     }
                 * }
                 */
                if (fireboundary && caller !== 'showprogress') {
                    spatialData["area"] = null
                    var tenure_area_task = tasks.find(task => task.taskId === 'tenure_area');
                    if (!tenure_area_task){
                        var tenure_area_task = vm._taskManager.addTask(feat,"getSpatialData","tenure_area","Calculate fire boundary areas",utils.WAITING)
                    }
                }

                if(caller === "showprogress"){
                    spatialData = vm.target_feature.spatial_data
                    var tenure_area_task = tasks.find(task => task.taskId === 'tenure_area');
                        if (vm.calculation_result["total_features"] > 0) {
                            var result = vm.calculation_result["features"][0]["area"]
                            if (result["status"]["failed"] ) {
                                //failed
                                tenure_area_task.setStatus(utils.FAILED,result["status"]["failed"])
                                vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                            } else if (result["status"]["invalid"]) {
                                //invalid geometry
                                vm._getValidationMessage = vm._getValidationMessage || function(message) {
                                    return "Geometry check of the fire shape has found the following error: " +
                                        "\r\n\t" + (Array.isArray(message)?message.join("\r\n\t"):message) +
                                        "\r\n\r\nPlease run a geometry check within ArcGIS before uploading" +
                                        "\r\nFor help contact the Fire Support Systems Team fire_systems_support@dbca.wa.gov.au";
                                }
                                var process_invalid_func = function(result) {
                                    var msg = vm._getValidationMessage(result["status"]["invalid"])
                                        vm.dialog.show({
                                            messages:msg,
                                            defaultOption:false,
                                            footer:[[
                                                ["",3],
                                                [false,2,{
                                                    type:"button",
                                                    title:"Ok",
                                                    click:"close"
                                                }],
                                                ["",2],
                                                [true,2,{
                                                    type:"button",
                                                    title:"Override",
                                                    click:"close"
                                                }],
                                                ["",3]
                                            ]],
                                            callback:function(option){
                                                if (option) {
                                                    setTimeout(function() {
                                                        vm.dialog.show({
                                                            messages:"I acknowledge a geometry check has been run and passed in ArcGIS Geometry Tool and this is a valid shape.",
                                                            defaultOption:false,
                                                            footer:[[
                                                                ["",3],
                                                                [true,2,{
                                                                    type:"button",
                                                                    title:"Yes",
                                                                    click:"close"
                                                                }],
                                                                ["",2],
                                                                [false,2,{
                                                                    type:"button",
                                                                    title:"Cancel",
                                                                    click:"close"
                                                                }],
                                                                ["",3]
                                                            ]],
                                                            callback:function(option){
                                                                setTimeout(function() {
                                                                    if (option) {
                                                                        result["data"]["fb_validation_req"] = true
                                                                        if (result["status"]["overlapped"]) {
                                                                            process_overlap_func(result)
                                                                        } else {
                                                                            spatialData["area"] = result["data"]
                                                                            tenure_area_task.setStatus(utils.SUCCEED)
                                                                            vm.showProgress(vm.target_feature)
                                                                        }
                                                                    } else {
                                                                        tenure_area_task.setStatus(utils.FAIL_CONFIRMED,msg)
                                                                        vm.showProgress(vm.target_feature)
                                                                    }
                                                                },1)
                                                            }
                                                        })
                                                    },1)
                                                } else {
                                                    tenure_area_task.setStatus(utils.FAIL_CONFIRMED,msg)
                                                    vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                                                }
                                            }
                                        })
                                    return
                                }
                                if(!vm.dialog.isActive && !spatialData["area"]){
                                    vm.taskDialog.close()
                                    process_invalid_func(result)
                                }
                            }
                            else if (result["status"]["overlapped"]) {
                                //found overlap
                                if(!vm.dialog.isActive && !spatialData["area"]){
                                    vm.taskDialog.close()
                                    feature_area = result["data"]
                                    vm.dialog.show({
                                        "title":"Error",
                                        messages:[
                                            "The calculated burnt area contains duplicate areas. Please contact fire_systems_support@dbca.wa.gov.au for assistance.",
                                            " ",
                                            "The sum of the burning areas in individual layers is " + Math.abs(feature_area["other_area"]).toFixed(2) + " greater than the total burning area " + feature_area["total_area"].toFixed(2) + ".",
                                            "The features from the following layers are overlaped.",
                                            [["",1],[vm.env.legislatedLandsAndWatersLayer,11]],
                                            [["",1],[vm.env.deptInterestLandsAndWatersLayer,11]],
                                            [["",1],[vm.env.otherTenuresLayer,11]],
                                            " ",
                                        ],
                                        defaultOption:false,
                                        footer:[[
                                            ["",2],
                                            [true,6,{
                                                type:"button",
                                                title:"Return to Edit Mode",
                                                click:function(button,data){
                                                    removed = vm.clearQueue(true)
                                                    if(removed){
                                                        vm.dialog.close();
                                                    }
                                                },
                                            }],
                                            [false,1,{
                                                type:"button",
                                                title:"Close",
                                                click:"close",
                                            }],
                                            ["",3]
                                        ]],
                                    })
                                }
                            } 
                            else {
                                result["data"]["fb_validation_req"] = null
                                spatialData["area"] = result["data"]
                                tenure_area_task.setStatus(utils.SUCCEED)
                                vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                            }
                        } else {
                            tenure_area_task.setStatus(utils.FAILED,"Calculate area failed.")
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                            //alert(tenure_area_task.message)
                        }
                    return
                }

                var tenure_origin_point_task = null
                var fire_position_task = null
                var originpoint_grid_task = null
                var region_task = null
                var district_task = null
                var plantation_task = null

                if (["new","initial"].indexOf(feat.get('status')) >= 0 )  {
                    spatialData["plantations"]  = null
                    if (originPoint)  {
                        plantation_task = tasks.find(task => task.taskId === 'plantation');
                        if (!plantation_task){
                            plantation_task = vm._taskManager.addTask(feat,"getSpatialData","plantation","Find the plantations within 3kms",utils.WAITING)  
                        }
                    }
                }
                if (originPoint && (modifyType & 1) === 1) {
                    tenure_origin_point_task = tasks.find(task => task.taskId === 'tenure_origin_point');
                    if (!tenure_origin_point_task){
                        tenure_origin_point_task = vm._taskManager.addTask(feat,"getSpatialData","tenure_origin_point","Get the tenure of ignition point",utils.WAITING)
                    }
                    fire_position_task = tasks.find(task => task.taskId === 'fire_position');
                    if (!fire_position_task){
                        fire_position_task = vm._taskManager.addTask(feat,"getSpatialData","fire_position","Get the fire position",utils.WAITING)
                    }
                    originpoint_grid_task = tasks.find(task => task.taskId === 'originpoint_grid');
                    if (!originpoint_grid_task){
                        originpoint_grid_task = vm._taskManager.addTask(feat,"getSpatialData","originpoint_grid","Get origin point's grid data",utils.WAITING)
                    }
                    if (["new","initial"].indexOf(feat.get('status')) >= 0) {
                        region_task = tasks.find(task => task.taskId === 'region');
                        if (!region_task){
                            region_task = vm._taskManager.addTask(feat,"getSpatialData","region","Get bushfire's region",utils.WAITING)
                        }
                        district_task = tasks.find(task => task.taskId === 'district');
                        if (!district_task){
                            district_task = vm._taskManager.addTask(feat,"getSpatialData","district","Get bushfire's district",utils.WAITING)
                        }
                    }
                }
                //need to call the callback first because the callback will not be called if no tasks are required.
                vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                if (tenure_area_task) {
                    tenure_area_task.setStatus(utils.RUNNING)
                    vm._getValidationMessage = vm._getValidationMessage || function(message) {
                        return "Geometry check of the fire shape has found the following error: " +
                            "\r\n\t" + (Array.isArray(message)?message.join("\r\n\t"):message) +
                            "\r\n\r\nPlease run a geometry check within ArcGIS before uploading" +
                            "\r\nFor help contact the Fire Support Systems Team fire_systems_support@dbca.wa.gov.au";
                    }
                    var process_overlap_func = function(result) {
                        //found overlap
                        feature_area = result["data"]
                        if (caller === "import") {
                            vm.dialog.show({
                                messages:[
                                    "The sum of the burning areas in individual layers is " + Math.abs(feature_area["other_area"]).toFixed(2) + " greater than the total burning area " + feature_area["total_area"].toFixed(2) + ".",
                                    "The features from the following layers are overlaped.",
                                    [["",1],[vm.env.legislatedLandsAndWatersLayer,11]],
                                    [["",1],[vm.env.deptInterestLandsAndWatersLayer,11]],
                                    [["",1],[vm.env.otherTenuresLayer,11]],
                                    "Do you want to continue?"
                                ],
                                defaultOption:false,
                                footer:[[
                                    ["",3],
                                    [true,2,{
                                        type:"button",
                                        title:"Yes",
                                        click:"close"
                                    }],
                                    ["",2],
                                    [false,2,{
                                        type:"button",
                                        title:"No",
                                        click:"close"
                                    }],
                                    ["",3]
                                ]],
                                callback:function(option){
                                    setTimeout(function() {
                                        if (option) {
                                            if (!("fb_validation_req" in feature_area)) {
                                                feature_area["fb_validation_req"] = null
                                            }
                                            spatialData["area"] = feature_area
                                            tenure_area_task.setStatus(utils.SUCCEED)
                                        } else {
                                            tenure_area_task.setStatus(utils.FAIL_CONFIRMED,"Cancelled")
                                        }
                                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                                    },1)
                                }
                            })
                            return
                        } else {
                            if (!("fb_validation_req" in feature_area)) {
                                feature_area["fb_validation_req"] = null
                            }
                            spatialData["area"] = feature_area
                            tenure_area_task.setStatus(utils.SUCCEED)
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                        }
                    }

                    var process_invalid_func = function(result) {
                        //invalid geometry
                        var msg = vm._getValidationMessage(result["status"]["invalid"])
                        if (caller === "import") {
                            vm.dialog.show({
                                messages:msg,
                                defaultOption:false,
                                footer:[[
                                    ["",3],
                                    [false,2,{
                                        type:"button",
                                        title:"Ok",
                                        click:"close"
                                    }],
                                    ["",2],
                                    [true,2,{
                                        type:"button",
                                        title:"Override",
                                        click:"close"
                                    }],
                                    ["",3]
                                ]],
                                callback:function(option){
                                    if (option) {
                                        setTimeout(function() {
                                            vm.dialog.show({
                                                messages:"I acknowledge a geometry check has been run and passed in ArcGIS Geometry Tool and this is a valid shape.",
                                                defaultOption:false,
                                                footer:[[
                                                    ["",3],
                                                    [true,2,{
                                                        type:"button",
                                                        title:"Yes",
                                                        click:"close"
                                                    }],
                                                    ["",2],
                                                    [false,2,{
                                                        type:"button",
                                                        title:"Cancel",
                                                        click:"close"
                                                    }],
                                                    ["",3]
                                                ]],
                                                callback:function(option){
                                                    setTimeout(function() {
                                                        if (option) {
                                                            result["data"]["fb_validation_req"] = true
                                                            if (result["status"]["overlapped"]) {
                                                                process_overlap_func(result)
                                                            } else {
                                                                spatialData["area"] = result["data"]
                                                                tenure_area_task.setStatus(utils.SUCCEED)
                                                                vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                                                            }
                                                        } else {
                                                            tenure_area_task.setStatus(utils.FAIL_CONFIRMED,msg)
                                                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                                                        }
                                                    },1)
                                                }
                                            })
                                        },1)
                                    } else {
                                        tenure_area_task.setStatus(utils.FAIL_CONFIRMED,msg)
                                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                                    }
                                }
                            })
                            return
                        } else if (caller === "batchimport") {
                            result["data"]["fb_validation_req"] = true
                            spatialData["area"] = result["data"]
                            tenure_area_task.setStatus(utils.SUCCEED)
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                        } else {
                            tenure_area_task.setStatus(utils.FAILED,msg)
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                        }

                    }
                    /*
                     * if grey bushfires not required to have area breakdown use this code.
                     * var layers = null
                     * if (["new","initial"].indexOf(feat.get('status')) >= 0 ) {
                     *     layers = null
                     * } else {
                     *     layers = [ ... ]
                     * }
                     */
                    var layers = [
                        {
                            id:"legislated_lands_and_waters",
                            layerid:vm.env.legislatedLandsAndWatersLayer,
                            cqlfilter:"LEG_CATEGORY<>'State Forest'",
                            kmiservice:getLayerUrl(vm.env.legislatedLandsAndWatersLayer, vm.env),
                            properties:{
                                category:"LEG_CATEGORY"
                            },
                            primary_key:"LEG_PIN"
                        },
                        {
                            id:"state_forest_plantation_distribution",
                            layerid:vm.env.stateForestPlantationDistributionLayer,
                            kmiservice:getLayerUrl(vm.env.stateForestPlantationDistributionLayer, vm.env),
                            properties:{
                                category:"FBR_FIRE_REPORT_CLASSIFICATION"
                            },
                        },
                        {
                            id:"dept_interest_lands_and_waters",
                            layerid:vm.env.deptInterestLandsAndWatersLayer,
                            kmiservice:getLayerUrl(vm.env.deptInterestLandsAndWatersLayer, vm.env),
                            properties:{
                                category:"LOI_CATEGORY"
                            },
                            primary_key:"LOI_PIN"
                        },
                        {
                            id:"other_tenures",
                            layerid:vm.env.otherTenuresLayer,
                            kmiservice:getLayerUrl(vm.env.otherTenuresLayer, vm.env),
                            properties:{
                                category:"BRC_FMS_Legend"
                            },
                        },
                        {
                            id:"sa_nt_burntarea",
                            layerid:vm.env.saNtStatePolygonsBurntAreaLayer,
                            kmiservice:getLayerUrl(vm.env.saNtStatePolygonsBurntAreaLayer, vm.env),
                            properties:{
                                category:"Name"
                            },
                        }
                    ]
                    $.ajax({
                        url: "/api/bfrs_calculation_queue",
                        dataType:"json",
                        data:{
                                bfrs:feat.get('fire_number'),
                                tasks:JSON.stringify(vm.featureTasks(vm.target_feature)),
                                features:vm.$root.geojson.writeFeatures([feat]),
                                options:JSON.stringify({
                                    area: {
                                        action:"getArea",
                                        layer_overlap:false,
                                        merge_result:true,
                                        unit:"ha",
                                        layers:layers
                                    }
                                })
                        },
                        method:"POST",
                        success: function (response, stat, xhr) {
                            var feature = vm.featurelist.find(f => f.get('fire_number') === feat.get('fire_number'));
                            if (feature) {
                                feature.set("original_status", feature.get("status"))
                                feature.set("status", "in_queue")
                                var import_task = tasks.find(task => task.taskId === 'import');
                                if (import_task){
                                    import_task.setStatus(utils.SUCCEED)
                                }
                                vm.showProgress(feature)
                            } else {
                                console.error("Feature not found");
                            }
                        },
                        error: function (xhr,status,message) {
                            alert((utils.FAILED,xhr.status + " : " + (xhr.responseText || message)))
                            if (xhr.status === 490) {
                                tenure_area_task.setStatus(utils.FAILED,vm._getValidationMessage(xhr.responseText || message))
                            } else {
                                tenure_area_task.setStatus(utils.FAILED,xhr.status + " : " + (xhr.responseText || message))
                            }
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                        },
                        xhrFields: {
                            withCredentials: true
                        }
                    })
                    
                }

                if (tenure_origin_point_task) {
                    tenure_origin_point_task.setStatus(utils.RUNNING)
                    tenure_layers = [{
                        id:vm.env.stateForestPlantationDistributionLayer,
                        geom_field:"wkb_geometry",
                        properties:{
                            id:"ogc_fid",
                            name:"fbr_fire_r",
                            category:"fbr_fire_r"
                        },
                        kb:{
                            geom_field:"SHAPE",
                            properties:{
                                name:"FBR_FIRE_REPORT_CLASSIFICATION",
                                category:"FBR_FIRE_REPORT_CLASSIFICATION"
                            }
                        },
                    },{
                        id:vm.env.legislatedLandsAndWatersLayer,
                        geom_field:"wkb_geometry",
                        properties:{
                            id:"ogc_fid",
                            name:"name",
                            category:"category"
                        },
                        kb:{
                            geom_field:"SHAPE",
                            properties:{
                                id:"LEG_PIN",
                                name:"LEG_NAME",
                                category:"LEG_CATEGORY"
                            }
                        },
                    },{
                        id:vm.env.deptInterestLandsAndWatersLayer,
                        geom_field:"wkb_geometry",
                        properties:{
                            id:"ogc_fid",
                            name:"name",
                            category:"category"
                        },
                        kb:{
                            geom_field:"SHAPE",
                            properties:{
                                id:"LOI_PIN",
                                name:"LOI_CATEGORY",
                                category:"LOI_CATEGORY"
                            }
                        },
                    },{
                        id:vm.env.otherTenuresLayer,
                        geom_field:"wkb_geometry",
                        properties:{
                            id:"ogc_fid",
                            name:"brc_fms_le",
                            category:"brc_fms_le"
                        },
                        kb:{
                            geom_field:"SHAPE",
                            properties:{
                                name:"BRC_FMS_Legend",
                                category:"BRC_FMS_Legend"
                            }
                        },
                    },{
                        id:vm.env.saNtStatePolygonsBurntAreaLayer,
                        geom_field:"wkb_geometry",
                        properties:{
                            id:"ogc_fid",
                            name:"name",
                            category:"name"
                        },
                        kb:{
                            geom_field:"SHAPE",
                            properties:{
                                name:"Name",
                                category:"Name"
                            }
                        },
                    }]
                    vm.map.getFeature(tenure_layers,originPoint,function(feature){
                        spatialData["tenure_ignition_point"] = feature
                        tenure_origin_point_task.setStatus(utils.SUCCEED)
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                    },
                    function(msg){
                        tenure_origin_point_task.setStatus(utils.FAILED,msg)
                        //alert(tenure_origin_point_task.message)
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                    })
                }

                if (fire_position_task) {
                    fire_position_task.setStatus(utils.RUNNING)
                    vm.map.getPosition(originPoint,function(position){
                        spatialData["fire_position"] = position
                        fire_position_task.setStatus(utils.SUCCEED)
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                    },
                    function(msg){
                        fire_position_task.setStatus(utils.FAILED,msg)
                        //alert(fire_position_task.message)
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                    })
                }
                if (originpoint_grid_task) {
                    originpoint_grid_task.setStatus(utils.RUNNING)
                    vm.map.getGridData(originPoint,function(grid_data){
                        spatialData["origin_point_grid"] = grid_data
                        originpoint_grid_task.setStatus(utils.SUCCEED)
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                    },
                    function(msg){
                        originpoint_grid_task.setStatus(utils.FAILED,msg)
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                    })
                }

                if (region_task) {
                    url_prefix = getLayerUrl(getLayerId(vm.env.regionLayer), vm.env)
                    var geom_name = (url_prefix === vm.env.kbService) ? "SHAPE" : "wkb_geometry";
                    region_task.setStatus(utils.RUNNING)
                    $.ajax({
                        url:url_prefix + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + getLayerId(vm.env.regionLayer) + "&outputFormat=json&cql_filter=CONTAINS(" + geom_name + ",POINT(" + originPoint[1]  + " " + originPoint[0] + "))",
                        dataType:"json",
                        success: function (response, stat, xhr) {
                            if (response.totalFeatures === 0) {
                                spatialData["region"] = null
                            } 
                            else {
                                spatialData["region"] = url_prefix === vm.env.kbService ? response.features[0].properties["DRG_REGION_NAME"] : response.features[0].properties["region"];   
                            }
                            region_task.setStatus(utils.SUCCEED)
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                        },
                        error: function (xhr,status,message) {
                            region_task.setStatus(utils.FAILED,xhr.status + " : " + (xhr.responseText || message))
                            //alert(region_task.message)
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                        },
                        xhrFields: {
                            withCredentials: true
                        }
                    })
                }

                if (district_task) {
                    url_prefix = getLayerUrl(getLayerId(vm.env.districtLayer), vm.env)
                    var geom_name = (url_prefix === vm.env.kbService) ? "SHAPE" : "wkb_geometry";
                    district_task.setStatus(utils.RUNNING)
                    $.ajax({
                        url:url_prefix + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + getLayerId(vm.env.districtLayer) + "&outputFormat=json&cql_filter=CONTAINS(" + geom_name + ",POINT(" + originPoint[1]  + " " + originPoint[0] + "))",
                        dataType:"json",
                        success: function (response, stat, xhr) {
                            if (response.totalFeatures === 0) {
                                spatialData["district"] = null
                            } else {
                                spatialData["district"] = url_prefix === vm.env.kbService ? response.features[0].properties["ADMIN_ZONE"] : response.features[0].properties["district"];
                                 
                            }
                            district_task.setStatus(utils.SUCCEED)
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                        },
                        error: function (xhr,status,message) {
                            district_task.setStatus(utils.FAILED,xhr.status + " : " + (xhr.responseText || message))
                            //alert(district_task.message)
                            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                        },
                        xhrFields: {
                            withCredentials: true
                        }
                    })
                }
            } catch(ex) {
                vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
            }

            if (plantation_task && caller !== 'showprogress') {
                plantation_task.setStatus(utils.RUNNING)
                var point_buffer = turf.buffer({
                    type:"Feature",
                    properties:{},
                    geometry:{
                        type:"Point",
                        coordinates:originPoint
                    }
                },3,"kilometers").geometry.coordinates[0]
                var plantationLayerId = vm.env.plantationAnnualReportLayer
                var isKbPlantation = getLayerUrl(plantationLayerId, vm.env) === vm.env.kbService
                var url = getLayerUrl(plantationLayerId, vm.env) + "/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + plantationLayerId + "&outputFormat=json&cql_filter=INTERSECTS(" + (isKbPlantation ? "SHAPE" : "wkb_geometry") + ",POLYGON((" + point_buffer.map(function(p){return p[1] + " " + p[0]}).join("%2C") + ")))"
                $.ajax({
                    url:url,
                    dataType:"json",
                    success: function (response, stat, xhr) {
                        if (response.totalFeatures > 0) {
                            //only send the properties to bfrs
                            spatialData["plantations"] = response.features.map(function(o){
                                if (isKbPlantation) {
                                    return {
                                        "ogc_fid":null,
                                        "species":o.properties["Species"],
                                        "sp_type":o.properties["Map_Symbol"],
                                        "area_ha":o.properties["AreaHa"],
                                        "classifica":o.properties["Classifica"]
                                    }
                                }
                                return {
                                    "ogc_fid":o.properties["ogc_fid"],
                                    "species":o.properties["species"],
                                    "sp_type":o.properties["sp_type"],
                                    "area_ha":o.properties["area_ha"],
                                    "classifica":o.properties["classifica"]

                                }
                            })
                        }
                        plantation_task.setStatus(utils.SUCCEED)
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                    },
                    error: function (xhr,status,message) {
                        plantation_task.setStatus(utils.FAILED,xhr.status + " : " + (xhr.responseText || message))
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,spatialData)
                    },
                    xhrFields: {
                        withCredentials: true
                    }
                })
            }
        }

        try {
            if (this.isFireboundaryDrawable(feat) || ((feat.get('modifyType') & 2) !== 2 && feat.get('fire_boundary')) && caller !== 'showprogress') {
                var tasks = vm.featureTasks(vm.target_feature);
                var validate_task = tasks.find(task => task.taskId === 'validate');
                if (!validate_task){
                    var validate_task = vm._taskManager.addTask(feat,"getSpatialData","validate","Validate bushfire",utils.RUNNING)
                }
                this.validateBushfire(feat,"getSpatialData",function(error) {
                    if (error) {
                        validate_task.setStatus(utils.FAILED,error)
                        //alert(error)
                        vm._getSpatialDataCallback(feat,caller,callback,failedCallback,{})
                    } else {
                        validate_task.setStatus(utils.SUCCEED)
                        vm._getSpatialData(feat,caller,callback,failedCallback)
                    }
                })
            } else {
                vm._getSpatialData(feat,caller,callback,failedCallback)
            }
        } catch(ex) {
            vm._getSpatialDataCallback(feat,caller,callback,failedCallback,{})
        }
      },
      saveFeature: function(feat,caller,callback) {
        if(feat.imported_feature){
            feat = feat.imported_feature
        }
        caller = caller || "save"
        if (this.canSave(feat) || caller === 'capturemethod') {
            var vm = this
            if (caller !== 'showprogress' && caller !== 'capturemethod') {
                vm.target_feature = vm.featurelist.find(f => f.get('fire_number') === feat.get('fire_number')) ||
                    vm.features.getArray().find(f => f.get('fire_number') === feat.get('fire_number')) || feat;
            } else if(!vm.target_feature || !feat.tasks){
                vm.target_feature = vm.featurelist.find(f => f.get('fire_number') === feat.get('fire_number')) ||
                    vm.features.getArray().find(f => f.get('fire_number') === feat.get('fire_number')) || feat;
            }
            var tasks = vm.featureTasks(vm.target_feature);
            
            //resetting tasks, if failed
            if (caller != 'showprogress' && caller != 'capturemethod' && tasks && tasks.length > 0) {
                for (let i = 0; i < tasks.length; i++) {
                    if (tasks[i].status === -1) {
                        feat.tasks = [];
                        break;
                    }
                }
            }

            //initialize feature tasks, if triggered by user
            if (!callback && !vm._taskManager.initTasks(feat)) {
                return
            }
            var task = tasks.find(task => task.taskId === 'save');
            if (!task) {
                //'save' task can be missing when this flow was entered via the background
                //processing/capturemethod path (e.g. origin-point-only edits) rather than the
                //user pressing "Save" first. Without it, task.setStatus() below would throw and
                //silently abort the completion chain, leaving the bushfire stuck as "Processing Finalised".
                var task = vm._taskManager.addTask(feat, "save", "save", "Save spatial data", utils.RUNNING);
            }
            if ((!vm.taskDialog || !vm.taskDialog.isActive) && caller !== 'showprogress') {
                vm.showProgress(feat);
            }
            if (!callback) {
                callback = function(feat,status,msg) {
                    if (status === utils.SUCCEED){
                        vm._taskManager.clearTasks(feat)
                        vm.resetFeature(feat,false)
                    } else if (status === utils.WARNING || status === utils.FAILED)  {
                        var msg = vm._taskManager.errorMessages(feat).join("\r\n")
                        if (msg) alert(msg)
                        if (status === utils.WARNING)  {
                            vm.resetFeature(feat,false)
                        }
                    }
                }
            }
            vm.getSpatialData(feat,caller,function(spatialData,job){
                if (!spatialData || Object.keys(spatialData).length === 0){
                    return
                }
                $.ajax({
                    url: vm.saveUrl(feat),
                    method:"PATCH",
                    data:JSON.stringify(spatialData),
                    contentType:"application/json",
                    success: function (response, stat, xhr) {
                        if (xhr.status === 280) {
                            //bushfire is invalidated, the new fire_number and id are returned
                            if (response.fire_number && response.id) {
                                feat.set("fire_number",response.fire_number)
                                feat.set("id",response.id)
                            } else {
                                task.setStatus(utils.FAILED,"The bushfire report is invalidated ,but the new fire_number and id are not returned.")
                                callback(feat,utils.FAILED,task.message)
                            }
                        }
                        if (!vm.isFireboundaryDrawable(feat)) {
                            if ((feat.get('modifyType') & 2) === 2) {
                                var originPoint = feat.getGeometry().getGeometries().find(function(g) {return g instanceof ol.geom.Point}) || null
                                if (originPoint) {
                                    var checkTask = tasks.find(task => task.taskId === 'check_originpoint');
                                    if (!checkTask){
                                        var checkTask = vm._taskManager.addTask(feat,"postsave","check_originpoint","Check origin within fire shape",utils.RUNNING)
                                    }
                                        originPoint = originPoint.getCoordinates()
                                        const layer_id = getLayerId(vm.env.bushfireFinalFireBoundaryLatestLayer);
                                        url = getLayerUrl(layer_id, vm.env);

                                        $.ajax({
                                        url:url + "/wfs?service=wfs&version=2.0&request=GetPropertyValue&valueReference=fire_number&typeNames=" + getLayerId(vm.env.bushfireFinalFireBoundaryLatestLayer) + "&cql_filter=(fire_number='" + feat.get('fire_number') + "')and (CONTAINS(fire_boundary,POINT(" + originPoint[1]  + " " + originPoint[0] + ")))",
                                        dataType:"xml",
                                        success: function (response, stat, xhr) {
                                                if (!response.firstChild || !response.firstChild.children || response.firstChild.children.length === 0) {
                                                checkTask.setStatus(utils.FAILED ,"Point of Origin is not inside fire boundary, please fix using the edit bushfire button")
                                                task.setStatus(utils.WARNING)
                                                callback(feat,utils.WARNING,checkTask.message)
                                                } else {
                                                checkTask.setStatus(utils.SUCCEED)
                                                task.setStatus(utils.SUCCEED)
                                                vm.clearQueue(withConfirm=false)
                                                callback(feat,utils.SUCCEED)
                                                }
                                            },
                                        error: function (xhr,status,message) {
                                            checkTask.setStatus(utils.FAILED,xhr.status + " : " + (xhr.responseText || message))
                                            task.setStatus(utils.WARNING)
                                            callback(feat,utils.WARNING,checkTask.message)
                                            },
                                            xhrFields: {
                                                withCredentials: true
                                            }
                                        })
                                    return
                                }
                            }
                        }

                        task.setStatus(utils.SUCCEED)
                        vm.clearQueue(false)
                        callback(feat,utils.SUCCEED)
                    },
                    error: function (xhr,status,message) {
                        task.setStatus(utils.FAILED,xhr.status + " : " + (xhr.responseText || message))
                        callback(feat,utils.FAILED,task.message)

                    },
                    xhrFields: {
                        withCredentials: true
                    }
                })
            })
                    
        }
      },
      newFireNumber: function(bushfireid,prefix) {
        bushfireid = Math.abs(bushfireid)
        return (prefix || "New bushfire") + " " + ((bushfireid < 10)?"00":(bushfireid < 100?"0":"")) + bushfireid
      },
      newFeature: function(feat) {
        var vm = this

        this._bushfireSequence = (this._bushfireSequence || 0)
        var featId = 0
        if (feat && feat.get('id')) {
            if (Math.abs(feat.get('id')) > this._bushfireSequence) {
                this._bushfireSequence = Math.abs(feat.get('id'))
            }
            featId = Math.abs(feat.get('id'))
        } else {
            this._bushfireSequence += 1
            featId = this._bushfireSequence
        }
        if (feat) {
            feat.set('status','new',true)
            feat.set('tint','new',true)
            feat.set('id',featId * -1,true)
            feat.set('originalTint','new',true)
            feat.set('toolName','Bfrs Origin Point',true)
            feat.set('fillColour',this.tints["new.fillColour"],true)
            feat.set('colour',this.tints["new.colour"],true)
            if (feat.getGeometry()) {
                feat.inViewport = ol.extent.containsCoordinate(vm.map.extent,vm.originpointCoordinate(feat))
            } else {
                feat.inViewport = false
            }
        } else {
            feat = new ol.Feature({
                geometry:new ol.geom.GeometryCollection([]),
                status:'new',
                tint:'new',
                id:this._bushfireSequence * -1,
                originalTint:'new',
                toolName:'Bfrs Origin Point',
                fillColour:this.tints["new.fillColour"],
                colour:this.tints["new.colour"],
            })
            feat.inViewport = true
        }

        feat.setStyle(this.bushfireStyleFunc)
        feat.set('modifyType',3,true)
        feat.set('fire_number',this.newFireNumber(featId),true)
        feat.set('name',this.newFireNumber(featId,"New bushfire report"),true)
        feat.set('report_status',99998,true)
        if (!feat.get('created')) {
            feat.set('created',new Date().toISOString(),true)
        }
        feat.set('fire_detected_or_created',feat.get('fire_detected_date') || feat.get('created'),true)
        feat.icon = '/static/dist/static/symbols/fire/dashed-origin.svg'

        vm._insertNewFeature = vm._insertNewFeature || function(features,feat){
            var insertIndex = null
            $.each(Array.isArray(features)?features:features.getArray(),function(index,f){
                if (vm.featureOrder(feat,f) === -1) {
                    insertIndex = index
                    return false
                }
            })
            if (insertIndex != null) {
                if (Array.isArray(features)) {
                    features.splice(insertIndex,0,feat)
                } else {
                    features.insertAt(insertIndex,feat)
                }
            } else {
                features.push(feat)
            }
        }

        vm._insertNewFeature(this.features,feat)
        //add to the feature list and map
        vm._insertNewFeature(this._featurelist,feat)
        if (vm.clippedFeatures.length > 0) {
            vm._insertNewFeature(this.clippedFeatures,feat)
        }
        return feat
      },
      createFeature: function(feat, caller) {
        caller = caller || "create"
        var vm = this;
        vm.target_feature = feat;

        function handleSpatialData(spatialData, task) {
            feat.set("modifyType", 0, true);
            if (!feat.get("sss_id")) {
                feat.set("sss_id", hash.MD5(vm.whoami["email"] + "-" + Date.now() + "-" + feat.getGeometry().getGeometriesArray()[0].getCoordinates().join(",")), true);
            }
            spatialData["sss_id"] = feat.get("sss_id");
            $("#sss_create").val(JSON.stringify(spatialData));
            utils.submitForm("bushfire_create");
            task.setStatus(utils.SUCCEED);
            if (vm.taskDialog) {
                vm.taskDialog.close();
            }
            vm._taskManager.clearTasks(feat);
            vm.clearQueue(withConfirm=false)
        }

        function handleError(task) {
            task.setStatus(utils.FAILED, "");
            var msg = vm._taskManager.errorMessages(feat).join("\r\n");
            if (msg) alert(msg);
        }

        if (caller === "showprogress") {
            var tasks = vm.featureTasks(feat);
            var task = tasks.find(task => task.taskId === 'create');
            this.getSpatialData(feat, "showprogress", function(spatialData, job) {
                handleSpatialData(spatialData, task);
            }, function(ex) {
                handleError(task);
            });
        } else {
            if (this.canCreate(feat)) {
                if (!vm._taskManager.initTasks(feat)) {
                    return;
                }
                var task = vm._taskManager.addTask(feat, "create", "create", "Open bushfire report form", utils.RUNNING);
                vm.showProgress(feat, "create");
                this.getSpatialData(feat, "create", function(spatialData, job) {
                    handleSpatialData(spatialData, task);
                }, function(ex) {
                    handleError(task);
                });
            }
        }
    },
      deleteFeature: function(feat) {
         var vm = this
         if (this.canDelete(feat)) {
            vm._deleteFeature = vm._deleteFeature || function(feat) {
                //console.log("Delete feature " + feat.get('label'))
                vm.selectedFeatures.remove(feat)
                //remove feature from list and map
                var index = vm.clippedFeatures.findIndex(function(f) {return f === feat})
                if (index >= 0) vm.clippedFeatures.splice(index,1)
                vm._featurelist.remove(feat)
                vm.features.remove(feat)
                vm.revision += 1
            }
            if (feat.get('status') === 'new') {
                vm._deleteFeature(feat)
            } else if (window.confirm('The bushfire (' + feat.get('label') + ' will be deleted. Are you sure?')) {
                $.ajax({
                    url: vm.deleteUrl(feat),
                    success: function (response, stat, xhr) {
                        vm._deleteFeature(feat)
                    },
                    error: function (xhr,status,message) {
                        alert(xhr.status + " : " + (xhr.responseText || message))
                    },
                    xhrFields: {
                      withCredentials: true
                    }
                })
            }
        }
      },
      resetFeature: function(feat, manually, callback) {
        var vm = this
        manually = (manually === undefined)?true:manually
        var filter = 'fire_number=\'' + feat.get('fire_number') + '\''
        if (this.bushfireLayer.cql_filter) {
            filter = filter + " and " + this.bushfireLayer.cql_filter
        }
        this.bushfireMapLayer.getSource().retrieveFeatures(filter,function(features){
          console.log("BFRS retrieveFeatures");
          console.log(features);
          if(feat.get('status') === 'in_queue' && feat.get('original_status') === 'new'){
            vm.target_feature = feat
            var clear_queue = vm.clearQueue(withConfirm=true)
                if(!clear_queue){
                    return
                }
            }
          if (features && features.length) {
            vm.initBushfire(features[0])
            features[0].inViewport = ol.extent.containsCoordinate(vm.map.extent,vm.originpointCoordinate(features[0]))
            if(feat.get('status') === 'in_queue'){
                vm.target_feature = feat
                var clear_queue = vm.clearQueue(withConfirm=true)
                if(!clear_queue){
                    return
                }
            }
            if (vm.taskDialog) {
                vm.taskDialog.close();
            }
            if (feat.selectedIndex !== undefined) {
                if (vm.annotations.getSelectedGeometry(features[0],feat.selectedIndex)) {
                    features[0].selectedIndex = feat.selectedIndex
                } else {
                    vm.selectDefaultGeometry(features[0])
                }
            }

            var index = vm.features.getArray().findIndex(function(f){return f.get('fire_number') === feat.get('fire_number')})
            if (index >= 0) {
                if (!manually && vm.features.item(index).tasks && vm.features.item(index).tasks.length > 0) {
                    features[0].tasks = vm.features.item(index).tasks
                }
                vm.features.setAt(index,features[0])
            }

            //features in layer's source is synchronized with _featurelist
            index = vm._featurelist.getArray().findIndex(function(f){return f.get('fire_number') === feat.get('fire_number')})
            if (index >= 0) {
                vm._featurelist.setAt(index,features[0])
                vm.revision += 1
            }

            index = vm.clippedFeatures.findIndex(function(f){return f.get('fire_number') === feat.get('fire_number')})
            if (index >= 0) {
                vm.clippedFeatures[index] = features[0]
                vm.revision += 1
            }

            index = vm.selectedFeatures.getArray().findIndex(function(f){return f.get('fire_number') === feat.get('fire_number')})
            if (index >= 0) {
                vm.selectedFeatures.setAt(index,features[0])
            }

            if (callback) {
                callback(features[0])
            }
            vm._checkPermission(features)
          } else {
            //feature does not exist or is invalid, remove it from bushfire list
            vm.selectedFeatures.remove(feat)
            vm._featurelist.remove(feat)
            var index = vm.clippedFeatures.findIndex(function(f) {return f === feat})
            if (index >= 0) vm.clippedFeatures.splice(index,1)
            vm.features.remove(feat)

            vm.revision += 1
            if (callback) {
                callback(null)
            }
          }
          vm.refreshFinalFireboundaryLayer()
        })
      },
      adjustHeight: function() {
        if (this.activeMenu === "bfrs") {
            //$("#bfrs-list").height(this.screenHeight - this.leftPanelHeadHeight - 16 - 16 - 4 - 5 - $("#bfrs-list-controller-container").height() - this.hintsHeight)
            $("#bfrs-list").height(this.screenHeight - this.leftPanelHeadHeight - 41 - $("#bfrs-list-controller-container").height() - this.hintsHeight)
        }
      },
      //modifyType(bit value):
      //    first bit:  origin point modified;
      //    second bit: fire boundary modified.
      //    -1: feature is drawed ,can't figure out which part of spatial data was modified
      postModified: function(bushfires,modifyType) {
        var vm = this
        this._bushfirePostModified = this._bushfirePostModified || function(bushfire,modifyType) {
            if (bushfire.get('tint') !== "modified" && (bushfire.get('status') !== "new" || bushfire.get("sss_id"))) {
                bushfire.set('tint',"modified",true)
                bushfire.set('fillColour',vm.tints[bushfire.get('tint') + ".fillColour"])
                bushfire.set('colour',vm.tints[bushfire.get('tint') + ".colour"])
            }
            if (modifyType === -1) {
                if (vm.isFireboundaryDrawable(bushfire)) {
                    //both fireboundary and point can be changed, don't which part of spatial data was changed,
                    modifyType = 3
                } else {
                    //only point can be changed.
                    modifyType = 1
                }
            }
            bushfire.set('modifyType',(bushfire.get('modifyType') || 0) | modifyType,true)
        }
        if (Array.isArray(bushfires)) {
            $.each(bushfires,function(index,bushfire){
                vm._bushfirePostModified(bushfire,modifyType)
            })
        } else {
            vm._bushfirePostModified(bushfires,modifyType)
        }
        vm.revision += 1
      },
      isModified: function(feat){
        return feat.get('tint') === 'modified'
      },
      toggleSelect: function (f) {
        if (this.isFeatureSelected(f)) {
          this.selectedFeatures.remove(f)
        } else {
          if (["Bfrs Origin Point","Bfrs Edit Geometry","Bfrs Fire Boundary"].indexOf(this.annotations.tool.name) >= 0) {
              //Only one bushfire can be choosed in edit mode
              this.selectedFeatures.clear()
          }
          this.selectedFeatures.push(f)
        }
        //this.zoomToSelected(200)
      },
      toggleViewportOnly: function () {
        this.viewportOnly = !this.viewportOnly
        this.export.saveState()
      },
      toggleBushfireLabels: function () {
        var vm = this
        this.bushfireLabels = !this.bushfireLabels
        this.export.saveState()
      },
      initBushfire: function(feature) {
        feature.set('status', this._reportStatus[feature.get('report_status') || 99999], true)

        var geometries = feature.getGeometry()?[feature.getGeometry()]:[]
        if (feature.get("fire_boundary")) { 
            var fire_boundary = feature.get("fire_boundary");          
            if (typeof fire_boundary === "string") {
                try {
                    fire_boundary = JSON.parse(fire_boundary);
                } catch (e) {
                    fire_boundary = null;
                }
            }
            if (fire_boundary && fire_boundary.coordinates) {
                if (!this.isFireboundaryDrawable(feature)) {
                    
                    var fbCoords = fire_boundary.coordinates;

                    var geom = fire_boundary.type === 'MultiPolygon'
                        ? new ol.geom.MultiPolygon(fbCoords)
                        : new ol.geom.MultiPolygon([fbCoords]);

                    feature.set("fire_boundary", geom.getExtent(), true);
                } else {
                    var fbCoords = fire_boundary.coordinates
                    geometries.push(
                        fire_boundary.type === 'MultiPolygon'
                            ? new ol.geom.MultiPolygon(fbCoords)
                            : new ol.geom.MultiPolygon([fbCoords])
                    )
                    feature.unset("fire_boundary", true)
                }
            } else {
                feature.unset("fire_boundary", true)
            }
        } else {
            feature.unset("fire_boundary", true)
        }
        feature.setGeometry(new ol.geom.GeometryCollection(geometries), true)
        var now = moment()
        var timestamp = moment(feature.get('created'))

        feature.set('toolName','Bfrs Origin Point', true)
        if (feature.get('status') == "merged") {
            feature.set('tint', this._reportStatus[feature.get('linked_bushfire_status')], true)
        } else {
            feature.set('tint', feature.get('status'), true)
        }
        feature.set('originalTint', feature.get('tint'), true)
        feature.set('fillColour', this.tints[feature.get('tint') + ".fillColour"])
        feature.set('colour', this.tints[feature.get('tint') + ".colour"])
        feature.setStyle(this.bushfireStyleFunc)
        if (feature.get('status') === 'initial' || (feature.get('status') === "merged" && feature.get("linked_bushfire_status") === 1)) {
            feature.icon = '/static/dist/static/symbols/fire/dashed-origin.svg'
        }
      },
	  
      showBushfireLabels: function() {
        if (this.bushfireMapLayer && !this.$root.active.isHidden(this.bushfireMapLayer)) {
            this.bushfireMapLayer.changed()
        }
      },
	  
      featureIconSrc: function(f) {
        var vm = this
        //trigger dynamic binding
        return this.map.getBlob(f, ['icon', 'originalTint'], this.tints, function(){
            $("#bushfire-icon-" + f.get('id')).attr("src", vm.featureIconSrc(f))
        })
      },
	  
      isFeatureSelected: function (f) {
        return this.selectedFeatures.getArray().findIndex(function(o){return o === f}) >= 0
      },
	  
      downloadList: function (fmt, downloadType) {
        var vm = this
        var cql_filter = ""
        this.dialog.show({
            messages:"Downloading bushfires...",
            footer:null
        })
        var bbox = ""
        var originpoint_filter = ""
        var fireboundary_filter = ""
        if (downloadType === "listed" || downloadType === "history" ) {
            if (
                this.clippedOnly ||
                (
                    (
                        vm._download_cql_filter ||
                        this.search && this.search.trim().length > 0 ||
                        (this.viewportOnly && this.extentFeaturesSize !== this.featureSizea)
                    ) &&
                    ((this.viewportOnly?this.extentFeaturesSize:this.featureSize) <= 80)
                )
            ){
                //use fire id as the filter if clipped only is true or has customer filter and the length of file list is less than 80
                var features = this._featurelist.getArray().filter(function(f) {
                    if (f.get('status') === 'new') {
                        return false
                    }
                    if (!vm.showFeature(f)) {
                        return false
                    }
                    return true
                })
                cql_filter = 'fire_number in (\'' + features.map(function(f){return f.get('fire_number')}).join('\',\'') + '\')'
                originpoint_filter = "&cql_filter=" + cql_filter
                fireboundary_filter = originpoint_filter
            } else {
                cql_filter = vm._download_cql_filter || ""
                if (this.search && this.search.trim().length > 0) {
                    cql_filter = (cql_filter?(cql_filter + " and (("):"((") +  this.fields.map(function(field) { return "strToLowerCase(" + field + ") like '%25" + vm.search.trim().toLowerCase() + "%25'"}).join(") or (") + "))"
                }
                if (cql_filter.length > 0) {
                    if (this.viewportOnly && this.extentFeaturesSize !== this.featureSize) {
                        bbox = this.map.extent
                        originpoint_filter = "&cql_filter=" + (cql_filter + " and BBOX(origin_point," + bbox[1] + "," + bbox[0] + "," + bbox[3] + "," + bbox[2] + ")")
                        fireboundary_filter = "&cql_filter=" + (cql_filter + " and BBOX(fire_boundary," + bbox[1] + "," + bbox[0] + "," + bbox[3] + "," + bbox[2] + ")")
                        bbox = ""
                    } else {
                        originpoint_filter = "&cql_filter=" + cql_filter
                        fireboundary_filter = originpoint_filter
                    }
                }

            }
            if (cql_filter.length === 0 && (this.viewportOnly && this.extentFeaturesSize !== this.featureSize)) {
                bbox = this.map.extent
                bbox = "&bbox=" + bbox[1] + "," + bbox[0] + "," + bbox[3] + "," + bbox[2]
            }
        }
        //console.log("originpoint filter = " + originpoint_filter)
        //console.log("bbox = " + bbox)
        var bushfireLayer = getLayerId((downloadType === "listed")?this.env.bushfireLatestLayer:this.env.bushfireLayer)
        var fireboundaryLayer = getLayerId((downloadType === "listed")?this.env.bushfireFireBoundaryLatestLayer:this.env.bushfireFireBoundaryLayer)
        var options = null
        if (downloadType === "history" ) {
            options = {
                filename:"bushfires_" + downloadType + "_" + moment().format('YYYY-MM-DD-HHmm'),
                srs:"EPSG:4326",
                layers:[{
                    layer:"bushfire_fireboundary",
                    ignore_if_empty:true,
                    sourcelayers:{
                        url:vm.env.kmiApiService + "/geoserver/wfs?servicea=wfs&version=2.0&request=GetFeature&typeNames=" + fireboundaryLayer + fireboundary_filter + bbox,
                        fields:["fire_number","name","district","financial_year","fire_detected_date","cause","dfes_incident_no","other_info",{name:"author",src:"fireboundary_uploaded_by"},"capt_meth","capt_desc"],
                    },
                    geometry_column:{name:"fire_boundary", type:"MULTIPOLYGON"},

                }]
            }
        } else {
            options = {
                filename: "bushfires_" + downloadType + "_" + moment().format('YYYY-MM-DD-HHmm'),
                srs: "EPSG:4326",
                layers: [{
                    layer: "initial_bushfire_originpoint",
                    ignore_if_empty: true,
                    sourcelayers: {
                        url:vm.env.kmiApiService + "/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + bushfireLayer + originpoint_filter  + bbox,
                        where:"report_status='Initial Fire Report'",
                    },
                    geometry_column: {name:"origin_point", type:"POINT"},
                },{
                    layer: "final_bushfire_originpoint",
                    ignore_if_empty: true,
                    sourcelayers: {
                        url: vm.env.kmiApiService + "/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + bushfireLayer + originpoint_filter + bbox,
                        where: "report_status<>'Initial Fire Report'",
                    },
                    geometry_column: {name:"origin_point", type:"POINT"},
                },{
                    layer:"initial_bushfire_fireboundary",
                    ignore_if_empty:true,
                    sourcelayers:{
                        url:vm.env.kmiApiService + "/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + fireboundaryLayer + fireboundary_filter + bbox,
                        where:"report_status='Initial Fire Report'",
                    },
                    geometry_column:{name:"fire_boundary", type:"MULTIPOLYGON"},
                },{
                    layer:"final_bushfire_fireboundary",
                    ignore_if_empty:true,
                    sourcelayers:{
                        url:vm.env.kmiApiService + "/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames=" + fireboundaryLayer + fireboundary_filter + bbox,
                        where:"report_status<>'Initial Fire Report'",
                    },
                    geometry_column:{name:"fire_boundary", type:"MULTIPOLYGON"},

                }]
            }
        }

        if (downloadType === 'listed') {
            var geometries = null
            var feature = null
            var id = 0
            var newBushfiresPoint = []
            var newBushfiresBoundary = []
            $.each(this._featurelist.getArray(),function(index,f){
                if (vm.showFeature(f) && f.get('status') == 'new') {
                    geometries = f.getGeometry().getGeometriesArray()

                    feature = vm.map.cloneFeature(f,false,['toolName','tint','originalTint','fillColour','colour','status','label','measurement','fire_boundary','modifyType'])
                    feature.setGeometry( geometries.find(function(g) {return g instanceof ol.geom.Point}) || null)
                    feature.setId(++id)
                    newBushfiresPoint.push(feature)

                    feature = vm.map.cloneFeature(feature,false)
                    feature.setGeometry(geometries.find(function(g){ return g instanceof ol.geom.MultiPolygon}) || new ol.geom.MultiPolygon())
                    feature.setId(++id)
                    newBushfiresBoundary.push(feature)
                }
            })
            if (newBushfiresPoint.length > 0 ) {
                options["newBushfiresOriginPoint"] = this.$root.geojson.writeFeatures(newBushfiresPoint)
                options["layers"].push({
                    layer:"new_bushfire_point",
                    ignore_if_empty:true,
                    sourcelayers:{
                        parameter:"newBushfiresOriginPoint",
                        srs:"EPSG:4326"
                    },
                    geometry_column:{name:"origin_point",type:"POINT"}
                })
            }
            if (newBushfiresBoundary.length > 0 ) {
                options["newBushfiresFireboundary"] = this.$root.geojson.writeFeatures(newBushfiresBoundary)
                options["layers"].push({
                    layer:"new_bushfire_fireboundary",
                    ignore_if_empty:true,
                    sourcelayers:{
                        parameter:"newBushfiresFireboundary",
                        srs:"EPSG:4326"
                    },
                    geometry_column:{name:"fire_boundary",type:"MULTIPOLYGON"}
                })
            }
        }
        this.$root.export.downloadVector(fmt,options,function(status,msg){
            if (status) {
                vm.dialog.close()
            } else {
                vm.dialog.addMessage(msg)
            }
        })
      },
      
	  uploadBushfire: function(targetFeature) {
        this._uploadBushfireNumber = targetFeature.get('fire_number')
        this._uploadType = "fireboundary"
        this._uploadTargetOnly = true
        $("#uploadBushfires").click()
      },

      updateTasks(targetFeature){
        var tasks = this.featureTasks(targetFeature);
        if(tasks){
            $.ajax({
                url: "/api/update_tasks.json",
                method: "GET",
                dataType: "json",
                data: { bfrs: targetFeature.get("fire_number"), 
                        tasks:JSON.stringify(tasks) },
            success: (response, stat, xhr) => {
            },
            error: function (xhr, status, message) {
                alert(xhr.status + " : " + (xhr.responseText || message)); 
                
            }
        });
      }
    },

        updateBfrsUploadProgress(){
            vm = this
            if(vm.target_feature){
                if (vm.taskDialog && vm.taskDialog.isActive && vm.target_feature.get('status') === 'in_queue') { 
                    vm.showProgress(vm.target_feature,'updateBfrsUploadProgress')
                }
            }
        },
        closeModal() {
            vm.taskDialog = null;
        },

    showProgress: function(targetFeature, caller) {
        caller = caller || "showprogress";
        var vm = this;
        var spatial_data = null;

        if(caller !== 'updateBfrsUploadProgress'){
            vm.progressRequestCount = 0;
        }

        if (targetFeature && targetFeature.spatial_data) {
            spatial_data = targetFeature.spatial_data;
        }
        

        var tasks = vm.featureTasks(targetFeature);
        var tenure_area_task = tasks.find(task => task.taskId === 'tenure_area');
        if (targetFeature.get('status') === 'new' || targetFeature.get('original_status') === 'new') {
            vm.completeButtonDisabled = true;
        }

        if (!tenure_area_task) {
            vm.feature_tasks = tasks;
            vm.clearButtonDisabled = true;
            vm.last_uploaded_date = '';
            vm.submitter = '';
            vm.calculation_status = '';
            vm.completeButtonDisabled = true;
            if(!vm.taskDialog.isActive){
                vm.taskDialog.open();
            }
        } else if(targetFeature.get('status') === 'in_queue') {
            if (vm.progressRequestPending) return
            vm.progressRequestPending = true
            vm.clearButtonDisabled = false;
            $.ajax({
                url: "/api/spatial_calculation_progress.json",
                method: "POST",
                dataType: "json",
                data: {
                    bfrs: targetFeature.get("fire_number"),
                    tasks: JSON.stringify(vm.featureTasks(targetFeature)),
                    spatial_data: JSON.stringify(spatial_data)
                },
                success: (response, stat, xhr) => {
                    vm.progressRequestPending = false;
                    var output = response['result'];
                    var status = response['status'];
                    var imp_feature = response['feature'];
                    var spatial_data = response['spatial_data'];
                    var retryForSpatialData = false;

                    vm.target_feature = targetFeature;
                    var tasks = vm.featureTasks(targetFeature);
                    var tenure_area_task = tasks.find(task => task.taskId === 'tenure_area');
                    var import_task = tasks.find(task => task.taskId === 'import');

                    if (import_task) {
                        import_task.setStatus(utils.SUCCEED);
                    }

                    vm.last_uploaded_date = response['last_uploaded_date'];
                    vm.submitter = response['submitter'];
                    vm.completeButtonDisabled = true;

                    if (tenure_area_task && tenure_area_task.status === 3 && targetFeature.spatial_data) {
                        vm.completeButtonDisabled = false;
                    }

                    if (status === "Imported") {
                        vm.calculation_status = "waiting";
                    }
                    if (status === "Calculating") {
                        vm.calculation_status = "calculating";
                    }
                    if(caller !== 'updateBfrsUploadProgress' && targetFeature.get('status') === 'in_queue'){
                        if(!vm.taskDialog.isActive){
                            vm.taskDialog.open();
                        }
                    }
                    if (status === "Calculation Error") {
                        vm.calculation_status = 'calculation_error';
                        if (response["error"]) {
                            tenure_area_task.setStatus(utils.FAILED, response["error"]);
                        } else {
                            tenure_area_task.setStatus(utils.FAILED);
                        }

                        tasks.forEach(task => {
                            if (task.taskId !== 'tenure_area' && task.status !== 3) {
                                task.setStatus(utils.FAILED);
                            }
                        });
                    }

                    if (status === "Processing Finalised") {
                        vm.calculation_status = 'calculation_completed';
                        if([1, 2, 3].includes(tenure_area_task.status)){
                            var parsedSpatialData = null;
                            try {
                                parsedSpatialData = typeof spatial_data === "string" ? JSON.parse(spatial_data) : spatial_data;
                            } catch (ex) {
                                parsedSpatialData = null;
                            }

                            if (!parsedSpatialData || Object.keys(parsedSpatialData).length === 0) {
                                vm.completeButtonDisabled = true;
                                retryForSpatialData = true;
                            } else {
                            Vue.set(vm.target_feature, 'spatial_data', parsedSpatialData);
                            tenure_area_task.setStatus(utils.SUCCEED);

                            var tasks = vm.featureTasks(targetFeature);
                            var allTasksCompleted = true;
                            tasks.forEach(task => {
                                if (task.taskId !== 'tenure_area' && task.status === -1) {
                                    allTasksCompleted = false;
                                }
                            });

                            if (!targetFeature.imported_feature) {
                                var feature_response = this.$root.geojson.readFeatures(imp_feature)[0];
                                targetFeature.imported_feature = feature_response;
                            }

                            var create_task = tasks.find(task => task.taskId === 'create');
                            if (create_task && targetFeature.imported_feature && allTasksCompleted) {
                                vm.completeButtonDisabled = true;
                                targetFeature.imported_feature.tasks = tasks;
                                vm.calculation_result = output;
                                vm.createFeature(targetFeature, "showprogress");
                            } else if (targetFeature.imported_feature && allTasksCompleted) {
                                vm.completeButtonDisabled = false;
                                targetFeature.imported_feature.tasks = tasks;
                                vm.calculation_result = output;
                                vm.saveFeature(targetFeature.imported_feature, "showprogress", () => {});
                            }
                            }
                        }
                    }

                    vm.feature_tasks = vm.featureTasks(vm.target_feature);

                    if (tenure_area_task.status === 2 || retryForSpatialData) {
                        let delay = vm.progressRequestCount === 0 ? 500 : 5000;
                        setTimeout(vm.updateBfrsUploadProgress, delay);
                    }
                    setTimeout(() => vm.updateTasks(vm.target_feature), 5000);
                    vm.progressRequestCount++;

                },
                error: function(xhr, status, message) {
                    vm.progressRequestPending = false;
                    alert(xhr.status + " : " + (xhr.responseText || message));
                    vm.progressRequestCount++;
                    setTimeout(vm.updateBfrsUploadProgress, 5000);
                },
                xhrFields: {
                    withCredentials: true,
                },
            });
        }
    },
   
    captureMethods() {
        if (this.completeButtonDisabled || !this.target_feature || !this.target_feature.spatial_data) {
            this.completeButtonDisabled = true;
            return;
        }
        selectedFeatures = []
        importedFinalFeatures = 0
        vm = this
        var feat = vm.target_feature
        var tasks = vm.featureTasks(feat)
        var import_task = tasks.find(task => task.taskId === 'import')
        var featureImported = function(status,message) {
            if (!import_task) {
                if (status === utils.SUCCEED) {
                    vm.dialog.addSucceedTask()
                } else if (status === utils.WARNING) {
                    vm.dialog.addWarningTask()
                } else if (status === utils.IGNORED) {
                    vm.dialog.addIgnoredTask()
                } else if (status === utils.MERGED) {
                    vm.dialog.addMergedTask()
                } else {
                    vm.dialog.addFailedTask()
                }
                if (message) {
                    vm.dialog.addMessage(message)
                }
                if (vm.dialog.tasks <= vm.dialog.succeedTasks) {
                    setTimeout(function(){vm.dialog.close()},1000);
                }
            } else if(message) {
                alert(message)
            }

            vm.selectedFeatures.clear()
            vm.selectedFeatures.extend(selectedFeatures)
            if (importedFinalFeatures > 0) {
                vm.refreshBushfires()
            }
            
        }
        this.saveFeature(feat,"capturemethod",function(f,status,msg) {
                vm.taskDialog.open()
                if (import_task) {
                    import_task.setStatus(status)
                }
                if (status === utils.SUCCEED) {
                    vm._taskManager.clearTasks(feat)
                }
                if (status === utils.SUCCEED || status === utils.WARNING) {
                    importedFinalFeatures += 1
                    selectedFeatures.push(feat)
                }
                if (import_task) {
                    msg = vm._taskManager.errorMessages(feat).join("\r\n")
                    if (msg) alert(msg)
                }
                featureImported(status)
            })      
    },
    clearQueue(withConfirm) {
        vm = this;
        feat = vm.target_feature;
        var removed = false;
        if ((!withConfirm || confirm("Do you want to remove the bush fire from processing?")) && feat.get('status') === 'in_queue') {
            if(withConfirm){
                removed = true;
            }
            $.ajax({
                url: "/api/clear_queue",
                dataType: "json",
                data: { bfrs: feat.get("fire_number"), status: vm.calculation_status, removed: removed },
                method: "POST",
                success: function (response, stat, xhr) {
                    if (feat) {
                        if(vm.taskDialog){
                            vm.taskDialog.close();
                        }
                        var target_feature = vm.featurelist.find(f => f.get('fire_number') === feat.get('fire_number'));
                        if(feat.get("original_status")){
                            feat.set("status", feat.get("original_status"))
                            target_feature.set("status", feat.get("original_status"))
                            target_feature.set('tint',feat.get("original_status"))
                            delete feat['original_status']
                            if(target_feature.get("orinal_status")){
                                delete target_feature['original_status']
                            }
                        }
                        if(withConfirm){
                            vm.resetFeature(target_feature, false)
                            target_feature.tasks = []
                        }
                        vm._taskManager.clearTasks(feat);
                    } else {
                        console.error("Feature not found");
                    }
                },
                error: function (xhr, status, message) {
                    alert(xhr.status + " : " + (xhr.responseText || message));
                },
            });
            if(vm.taskDialog || vm.taskDialog.isActive){
                vm.taskDialog.close()
            }
            return true;
        }
        return false;
    },

	  importList: function () {
        if (this.$els.bushfiresfile.files.length === 0) {
            return
        }
        var file = this.$els.bushfiresfile.files[0]
        this.$els.bushfiresfile.value = null
        var vm = this
        var targetFeature = null
        if (this._uploadBushfireNumber) {
            targetFeature = this.features.getArray().find(function(f) {return f.get('fire_number') === vm._uploadBushfireNumber})
            delete this._uploadBushfireNumber
            if (!targetFeature) {
                alert("Bushfire (" + this._uploadBushfireNumber + ") does not exist in the bushfire list.")
                return
            }
        }

        var uploadType = this._uploadType
        delete this._uploadType
        var targetOnly = (targetFeature && this._uploadTargetOnly)?true:false
        delete this._uploadTargetOnly
        var import_task = null
        if (targetFeature) {
            if (!this._taskManager.initTasks(targetFeature)) {
                return
            }
            var tasks = this.featureTasks(targetFeature);
            this.target_feature = targetFeature
            import_task = this._taskManager.addTask(targetFeature,"import","import","Import bushfire fire boundary",utils.RUNNING)

        }
        vm.dialog.show({
            title:"Importing bushfires...",
            footer:null
        })
        vm.export.importVector(file,function(features,fileFormat){
          try{
            vm.dialog.close()
            if (targetFeature) {
                targetFeature = vm.features.getArray().find(function(f) {return f.get('fire_number') === targetFeature.get('fire_number')})
                if (!targetFeature) {
                    alert("Bushfire (" + targetFeature.get('fire_number') + ") does not exist in the bushfire list.")
                    return
                }
            }

            var importedFinalFeatures = 0
            var importingFeatures = features.length
            var selectedFeatures = []
            if (!import_task && features.length > 0) {
                vm.dialog.show({
                    messages:"Importing bushfires...",
                    tasks: features.length,
                    footer:null
                })
            }
            var featureImported = function(status,message) {
                if (!import_task) {
                    if (status === utils.SUCCEED) {
                        vm.dialog.addSucceedTask()
                    } else if (status === utils.WARNING) {
                        vm.dialog.addWarningTask()
                    } else if (status === utils.IGNORED) {
                        vm.dialog.addIgnoredTask()
                    } else if (status === utils.MERGED) {
                        vm.dialog.addMergedTask()
                    } else {
                        vm.dialog.addFailedTask()
                    }
                    if (message) {
                        vm.dialog.addMessage(message)
                    }
                    if (vm.dialog.tasks <= vm.dialog.succeedTasks) {
                        setTimeout(function(){vm.dialog.close()},1000);
                    }
                } else if(message) {
                    alert(message)
                }

                importingFeatures -= 1
                if (importingFeatures <= 0) {
                    vm.selectedFeatures.clear()
                    vm.selectedFeatures.extend(selectedFeatures)
                    if (importedFinalFeatures > 0) {
                        vm.refreshBushfires()
                    }
                }
            }

            var f = null
            //initialize the loaded features
            var properties = null
            if (fileFormat === "gpx") {
                //gpx file
                if (uploadType === "originpoint") {
                    features.length = 0
                }
                for(var i = features.length - 1;i >= 0;i--) {
                    feature = features[i]
                    if (targetFeature) {
                        feature.set('fire_number',targetFeature.get('fire_number'),true)
                        feature.set('id',targetFeature.get('id'),true)
                    }
                    if (uploadType === "originpoint") {
                        features.splice(i,1)
                        featureImported(utils.IGNORED)
                        continue
                    }
                    if (feature.getGeometry() instanceof ol.geom.Point) {
                        //feature.set('toolName','Spot Fire')
                        featureImported(utils.IGNORED)
                        features.splice(i,1)
                    } else if(feature.getGeometry() instanceof ol.geom.LineString) {
                        var coordinates = feature.getGeometry().getCoordinates()
                        coordinates.push(coordinates[0])
                        feature.setGeometry(new ol.geom.Polygon([coordinates]))
                    } else if(feature.getGeometry() instanceof ol.geom.MultiLineString) {
                        var geom = feature.getGeometry()
                        var coordinates = null
                        var mp = new ol.geom.MultiPolygon()
                        $.each(geom.getLineStrings(),function(index,linestring) {
                            coordinates = linestring.getCoordinates()
                            if (coordinates[coordinates.length - 1][0] !== coordinates[0][0] || coordinates[coordinates.length - 1][1] !== coordinates[0][1]) {
                                coordinates.push(coordinates[0])
                            }
                            mp.appendPolygon(new ol.geom.Polygon([coordinates]))
                        })
                        feature.setGeometry(mp)
                    } else {
                        featureImported(utils.IGNORED)
                        features.splice(i,1)
                    }
                }
            } else {
                //geo json file
                //try to figure out the property name of 'fire_number','capt_meth' and 'capt_desc' in imported files
                var property = null
                properties = ['fire_number','capt_meth','capt_desc'] //list the properties, you want to find, from the longest property to shortest property
                var propertyLen = null //
                $.each(properties,function(index,prop){
                    property = null
                    if (propertyLen === null) {
                        for(var i = prop.length;i >= 8;i--) {
                            var name = prop.substring(0,i)
                            for (var j = 0;j < features.length;j++) {
                                if (features[j].get(name) !== undefined) {
                                    property = name
                                    break
                                }
                            }
                            if (property) {
                                break
                            }
                        }
                        if (property !== null) {
                            //found property from one feature, because properties are listed from longest to shortest,
                            //set the length of this property as the max property len to avoid to seach the property name in features for each property
                            propertyLen = property.length
                        }
                    } else if (prop.length <= propertyLen){
                        //property name is not changed
                        return
                    } else {
                        //property name is changed.
                        property = prop.substring(0,propertyLen)
                    }
                    property = property || prop
                    if (property !== prop) {
                        //for some reason, the name of property is changed', change the name of property to prop we wanted
                        //for example, in shape file, the name of fire_number property is 'fire_numbe' because of the property length limit
                        for (var j = 0;j < features.length;j++) {
                            if (features[j].get(property) !== undefined) {
                                features[j].set(prop,features[j].get(property),true)
                                features[j].unset(property)
                            }
                        }
                    }
                })

                targetFeatureFound = false
                for(var i = features.length - 1;i >= 0;i--) {
                    feature = features[i]
                    if (targetFeature && (feature.get('fire_number') === undefined || feature.get('fire_number') === null)) {
                        feature.set('fire_number',targetFeature.get('fire_number'),true)
                        feature.set('id',targetFeature.get('id'),true)
                    }
                    if (targetOnly && feature.get('fire_number') !== targetFeature.get('fire_number')) {
                        //not target feature, ignore
                        features.splice(i,1)
                        featureImported(utils.IGNORED)
                        continue
                    }  else if (targetOnly){
                        targetFeatureFound = true
                    }
                    if (feature.getGeometry() instanceof ol.geom.Point) {
                        if (uploadType === "fireboundary") {
                            featureImported(utils.IGNORED)
                            features.splice(i,1)
                        }
                    } else if (feature.getGeometry() instanceof ol.geom.Polygon) {
                        if (uploadType === "originpoint") {
                            featureImported(utils.IGNORED)
                            features.splice(i,1)
                        }
                    } else if (feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                        if (uploadType === "originpoint") {
                           featureImported(utils.IGNORED)
                            features.splice(i,1)
                        }
                    } else if (feature.getGeometry() instanceof ol.geom.GeometryCollection) {
                        //remove the MultiPoint feature
                        features.splice(i,1)
                        //split the gemoetry collection into mutiple features
                        var geometries = null
                        geometries = feature.getGeometry().getGeometries()

                        //split MultiPoint to multiple point feature
                        $.each(geometries,function(index,geometry){
                            f = new ol.Feature({ geometry:geometry})
                            features.splice(i,0,f)
                            i += 1
                        })
                        vm.dialog.addTasks(geometries.length - 1)
                    } else {
                        featureImported(utils.IGNORED)
                        features.splice(i,1)
                    }
                }
            }
            if (features && features.length == 0) {
                if (targetFeature) {
                    if (targetFeatureFound) {
                        import_task.setStatus(utils.WARNING,"No suitable spataial data for Bushfire(" + targetFeature.get('fire_number') + ") in uploaded file.")
                    } else {
                        import_task.setStatus(utils.WARNING,"Bushfire(" + targetFeature.get('fire_number') + ") not found")
                    }
                    vm._taskManager.clearTasks(targetFeature)
                } else {
                    alert("No bushfire to import")
                }
            } else {
                //Combine multiple features of bushfire into one feature.
                features.sort(function(f1,f2){
                    var id1 = f1.get('fire_number')
                    var id2 = f2.get('fire_number')
                    if (id1) {
                        if (id2) {
                            return (id1 === id2)?0:(id1 < id2 ?-1:1)
                        } else {
                            return 1
                        }
                    } else if(id2) {
                        reurn -1
                    } else {
                        return 0
                    }
                })

                var mergeProperties = function(feat1,feat2) {
                    $.each(properties,function(index,prop){
                        if (feat2.get(prop) !== undefined) {
                            feat1.set(prop,feat2.get(prop),true)
                        }

                    })
                }

                var feat = null
                for(var i = features.length - 1;i >= 0;i--) {
                    if (feat &&
                        (
                            feat.get('fire_number') === features[i].get('fire_number') && features[i].get('fire_number') !== undefined && features[i].get('fire_number') !== null
                        )
                    ) {
                        if (features[i].getGeometry() instanceof ol.geom.Point) {
                            if (feat.getGeometry() instanceof ol.geom.MultiPolygon) {
                                feat.setGeometry(new ol.geom.GeometryCollection([features[i].getGeometry(),feat.getGeometry()]))
                                mergeProperties(feat,features[i])
                                features.splice(i,1)
                                featureImported(utils.MERGED)
                            } else {
                                //already have a point, ignore the point
                                features.splice(i,1)
                                featureImported(utils.IGNORED)
                            }
                        } else if (features[i].getGeometry() instanceof ol.geom.Polygon) {
                            if (feat.getGeometry() instanceof ol.geom.MultiPolygon) {
                                feat.getGeometry().appendPolygon(features[i].getGeometry())
                                mergeProperties(feat,features[i])
                                features.splice(i,1)
                            } else if (feat.getGeometry() instanceof ol.geom.Point) {
                                feat.setGeometry(new ol.geom.GeometryCollection([feat.getGeometry(),new ol.geom.MultiPolygon([features[i].getGeometry().getCoordinates()])]))
                                mergeProperties(feat,features[i])
                                features.splice(i,1)
                            } else if (feat.getGeometry() instanceof ol.geom.GeometryCollection) {
                                feat.getGeometry().getGeometriesArray()[1].appendPolygon(features[i].getGeometry())
                                mergeProperties(feat,features[i])
                                features.splice(i,1)
                            }
                            featureImported(utils.MERGED)
                        } else if (features[i].getGeometry() instanceof ol.geom.MultiPolygon) {
                            if (feat.getGeometry() instanceof ol.geom.MultiPolygon) {
                                $.each(features[i].getGeometry().getPolygons(),function(index,p) {
                                    feat.getGeometry().appendPolygon(p)
                                })
                                mergeProperties(feat,features[i])
                                features.splice(i,1)
                            } else if (feat.getGeometry() instanceof ol.geom.Point) {
                                feat.setGeometry(new ol.geom.GeometryCollection([feat.getGeometry(),features[i].getGeometry()]))
                                mergeProperties(feat,features[i])
                                features.splice(i,1)
                            } else if (feat.getGeometry() instanceof ol.geom.GeometryCollection) {
                                $.each(features[i].getGeometry().getPolygons(),function(index,p) {
                                    feat.getGeometry().getGeometriesArray()[1].appendPolygon(p)
                                })
                                mergeProperties(feat,features[i])
                                features.splice(i,1)
                            }
                            featureImported(utils.MERGED)
                        }
                    } else {
                        feat = features[i]
                        if (feat.getGeometry() instanceof ol.geom.Polygon) {
                            feat.setGeometry(new ol.geom.MultiPolygon([feat.getGeometry().getCoordinates()]))
                        }
                    }

                }

                //after merged, loaded feature can have geometryCollection,  point or multipolygon
                //update existing bushfires

                var canUpload = function(uploadedFeature,feature) {
                    if (feature && !vm.isFireboundaryDrawable(feature)) {
                        return
                    }
                    var uploadedFireboundary = null
                    if(uploadedFeature.getGeometry() instanceof ol.geom.GeometryCollection) {
                        uploadedFireboundary = uploadedFeature.getGeometry().getGeometriesArray()[1]
                    } else if(uploadedFeature.getGeometry() instanceof ol.geom.MultiPolygon) {
                        uploadedFireboundary = uploadedFeature.getGeometry()
                    }
                    if (!uploadedFireboundary) {
                        return
                    }
                    uploadedFireboundary = uploadedFireboundary.getCoordinates()
                    var points = 0
                    for (var pIndex = 0;pIndex < uploadedFireboundary.length;pIndex++) {
                        for(var rIndex = 0;rIndex < uploadedFireboundary[pIndex].length;rIndex++) {
                            points += uploadedFireboundary[pIndex][rIndex].length
                        }
                    }
                    if (points > 5000) {
                        if (feature) {
                            throw "The initial bushfire(" + uploadedFeature.get('fire_number') + ") has more than 5000 vertex points."
                        } else {
                            throw "A uploaded new bushfire has more than 5000 vertex points."
                        }
                    }
                }
                if (!targetFeature) {
                    if (vm.search && vm.search.trim().length > 0) {
                        vm.search = ""
                        vm.clippedOnly = false
                        vm.updateFeatureFilter(3,0)
                    } else if (vm.clippedOnly) {
                        vm.clippedOnly = false
                        vm.updateFeatureFilter(1,0)
                    }
                }
                //var notFoundBushfires = null
                //var noPermissionBushfires = null
                var geometries = null
                $.each(features,function(index,feature){
                    if (feature.get('fire_number') !== undefined) {
                        //existed bushfire report
                        try {
                            var feat = vm.features.getArray().find(function(f) {return f.get('fire_number') === feature.get('fire_number')})
                            canUpload(feature,feat)
                            if (feat) {
                                if (!vm.isModifiable(feat)) {
                                    featureImported(utils.IGNORED)
                                    return
                                }
                                changed = false
                                geometries = feat.getGeometry().getGeometriesArray()
                                featurePoint = geometries.find(function(g){return g instanceof ol.geom.Point}) || null
                                if (vm.isFireboundaryDrawable(feat)) {
                                    featureFireboundary = geometries.find(function(g){return g instanceof ol.geom.MultiPolygon}) || null
                                } else {
                                    featureFireboundary = feat.get('fire_boundary')
                                }
                                var uploadedPoint = null
                                var uploadedFireboundary = null
                                if (feature.getGeometry() instanceof ol.geom.Point) {
                                    uploadedPoint = feature.getGeometry()
                                } else if(feature.getGeometry() instanceof ol.geom.GeometryCollection) {
                                    uploadedPoint = feature.getGeometry().getGeometriesArray()[0]
                                    uploadedFireboundary = feature.getGeometry().getGeometriesArray()[1]
                                } else if(feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                                    uploadedFireboundary = feature.getGeometry()
                                }
                                var modifyType = 0
                                if (uploadedPoint && !vm.map.isGeometryEqual(uploadedPoint,featurePoint,0.000000005)) {
                                    modifyType = modifyType | 1
                                }
                                if (uploadedFireboundary && (!vm.isFireboundaryDrawable(feat) || !vm.map.isGeometryEqual(uploadedFireboundary,featureFireboundary,0.000000005))) {
                                    modifyType = modifyType | 2
                                }
                                if(feature.get('crs')){
                                    feat.set('crs', feature.get('crs'))
                                }
                                if (!vm.isFireboundaryDrawable(feat) && (modifyType & 2) === 2) {
                                    //save to the database directly
                                    feature.set('id',feat.get('id'),true)
                                    feature.set('status',feat.get('status'),true)
                                    feature.set('report_status',feat.get('report_status'),true)
                                    feature.set('fire_number',feat.get('fire_number'),true)
                                    feature.set('modifyType',modifyType | (feat.get('modifyType') || 0),true)
                                    feature.set('tint','modified',true)
                                    feature.set('fire_boundary',uploadedFireboundary.getExtent(),true)
                                    feature.set('external_feature',true)
                                    newGeometries = []
                                    if ((modifyType & 1) === 1) {
                                        //both fireboundary and origin point are changed
                                        feature.setGeometry(new ol.geom.GeometryCollection([uploadedPoint,uploadedFireboundary]))
                                    } else if (featurePoint) {
                                        //only fire boundary is changed, feature already has a valid origin point
                                        feature.setGeometry(new ol.geom.GeometryCollection([featurePoint,uploadedFireboundary]))
                                    } else {
                                        //only fire boundary is changed, feature does not have a valid origin point
                                        feature.setGeometry(new ol.geom.GeometryCollection([uploadedFireboundary]))
                                    }
                                    if (!targetFeature && !vm._taskManager.initTasks(feat)) {
                                        featureImported(utils.IGNORED)
                                        return
                                    }
                                    feature.tasks = feat.tasks
                                    var target_feature = vm.featurelist.find(f => f.get('fire_number') === feat.get('fire_number'));
                                    target_feature.imported_feature = feature
                                    vm.saveFeature(feature,targetFeature?"import":"batchimport",function(f,status,msg){
                                        if (import_task) {
                                            import_task.setStatus(status)
                                        }
                                        if (status === utils.SUCCEED) {
                                            vm._taskManager.clearTasks(feat)
                                        }
                                        if (status === utils.SUCCEED || status === utils.WARNING) {
                                            importedFinalFeatures += 1
                                            selectedFeatures.push(feat)
                                        }
                                        if (import_task) {
                                            msg = vm._taskManager.errorMessages(feat).join("\r\n")
                                            if (msg) alert(msg)
                                        }
                                        featureImported(status)
                                    })
                                } else {
                                    if ((modifyType & 1) === 1) {
                                        if (featurePoint) {
                                            geometries[0] = uploadedPoint
                                        } else {
                                            geometries.splice(0,0,uploadedPoint)
                                        }
                                    }
                                    if ((modifyType & 2) === 2) {
                                        if (featureFireboundary){
                                            geometries[1] = uploadedFireboundary
                                        } else {
                                            geometries.push(uploadedFireboundary)
                                        }
                                    }
                                    selectedFeatures.push(feat)
                                    if (modifyType > 0) {
                                        feat.getGeometry().setGeometriesArray(geometries)
                                        vm.postModified(feat,modifyType)
                                    }
                                    if (import_task) {
                                        import_task.setStatus(utils.SUCCEED)
                                        vm._taskManager.clearTasks(feat)
                                    }
                                    featureImported(utils.SUCCEED)
                                }
                            } else if(feature.get('id') < 0 && vm.newFireNumber(feature.get('id')) === feature.get('fire_number') && vm.isCreatable()) {
                                if (vm.isCreatable()) {
                                    //new feature,
                                    if (feature.getGeometry() instanceof ol.geom.Point || feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                                        feature.setGeometry(new ol.geom.GeometryCollection([feature.getGeometry()]))
                                    }
                                    vm.newFeature(feature)
                                    //vm.measure.remeasureFeature(feature)
                                    selectedFeatures.push(feature)
                                    featureImported(utils.SUCCEED)
                                } else {
                                    featureImported(utils.IGNORED)
                                }
                            } else {
                                //notFoundBushfires = notFoundBushfires || []
                                //notFoundBushfires.push(feature)
                                featureImported(utils.IGNORED)
                            }
                        } catch(ex) {
                            featureImported(utils.FAILED,ex.message || ex)
                        }
                    }
                })
                //add non existing bushfires
                $.each(features,function(index,feature){
                    if (feature.get('fire_number') === undefined) {
                        if (vm.isCreatable()) {
                            //non existed bushfire report
                            try {
                                canUpload(feature,null)
                                if (feature.getGeometry() instanceof ol.geom.Point || feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                                    feature.setGeometry(new ol.geom.GeometryCollection([feature.getGeometry()]))
                                }
                                vm.newFeature(feature)
                                //vm.measure.remeasureFeature(feature)
                                selectedFeatures.push(feature)
                                featureImported(utils.SUCCEED)
                            } catch(ex) {
                                featureImported(utils.FAILED,ex.message || ex)
                            }
                        } else {
                            featureImported(utils.IGNORED)
                        }
                    }
                })

                if (import_task && vm._taskManager.getTasks(targetFeature).length === 1) {
                    import_task.setStatus(utils.SUCCEED)
                    vm._taskManager.clearTasks(targetFeature)
                }
                /*
                if (notFoundBushfires) {
                    alert("Some bushfires are not found." + JSON.stringify(notFoundBushfires.map(function(o) {return {id:o.get('id'),name:o.get('name')}})))
                }
                */
            }
          }catch(ex) {
            if (import_task) {
                import_task.setStatus(utils.FAILED,ex.message || ex)
            }
            if (targetFeature) {
                vm._taskManager.clearTasks(targetFeature)
            }
            vm.dialog.addMessage(ex.message||ex)
          }
        },
        function(ex) {
            if (ex !== "Cancelled") {
                alert(ex)
            }
            if (import_task) {
                import_task.setStatus(utils.FAILED,ex.message || ex)
            }
            if (targetFeature) {
                vm._taskManager.clearTasks(targetFeature)
            }
            if (vm.dialog){
                setTimeout(function(){vm.dialog.close()},100);
            }
        }, true)
      },
      
    resetFilters: function() {
        this.region = ""
        this.district = ""
        this.dateRange = "70001"
        this.changeDateRange()
        this.statusFilter = "all_reports"
        this.updateCQLFilter(0)
      },      
	  refreshBushfires: function() {
        this.isFeatureListLoading = true
        this.bushfireMapLayer.getSource().loadSource("query")
        this.refreshFinalFireboundaryLayer()
        if (this.selectedFeatures.getLength() > 0) {
            this.refreshSelectedFinalFireboundaryLayer()
        }
      },      
	  updateCQLFilter: function (wait, force, callback) {
        var vm = this
        if (!vm._updateCQLFilterFunc) {
            vm._updateCQLFilterFunc = function(force, callback){
                try{
                    if (!vm.bushfireMapLayer) {
                        vm._updateCQLFilter.call({wait:100}, force, callback)
                        return
                    }
                    // CQL statement assembling logic
                    var filters = [vm._statusFilters[vm.statusFilter][0], vm.regionFilter(), vm.districtFilter(), vm.dateFilter()].filter(function(f){return (f || false) && true})
                    var cql_filter = ''
                    if (filters.length === 0) {
                      cql_filter = ''
                    } else if (filters.length === 1) {
                      cql_filter = filters[0]
                    } else {
                      cql_filter = "(" + filters.join(") and (") + ")"
                    }
                    if (!force && vm.bushfireLayer.cql_filter === cql_filter) {
                        //not changed
                        return
                    } else {
                        vm.bushfireLayer.cql_filter = cql_filter
                        filters = [
                            vm._statusFilters[vm.statusFilter][1],
                            vm.regionFilter(true),
                            vm.districtFilter(true),
                            vm.dateFilter()
                        ].filter(function(f){return (f || false) && true})
                        cql_filter = ''
                        if (filters.length === 0) {
                          cql_filter = ''
                        } else if (filters.length === 1) {
                          cql_filter = filters[0]
                        } else {
                          cql_filter = "(" + filters.join(") and (") + ")"
                        }
                        vm._download_cql_filter = cql_filter
                    }
                    //clear bushfire filter or change other filter
                    vm.isFeatureListLoading = true
                    vm.bushfireMapLayer.getSource().loadSource("query", callback)
                } catch(ex) {
                    vm.isFeatureListLoading = false
                    //ignore the exception
                    //alert(ex)
                }
            }
        }

        if (!vm._updateCQLFilter) {
            vm._updateCQLFilter = debounce(function(force,callback){
                vm._updateCQLFilterFunc(force,callback)
            },2000)
        }
        if (wait === 0) {
            vm._updateCQLFilterFunc(force,callback)
        } else if (wait === undefined || wait === null) {
            vm._updateCQLFilter(force,callback)
        } else {
            vm._updateCQLFilter.call({wait:wait},force,callback)
        }
      },
      
	  featureOrder: function (a, b) {
        if (a.get('status') === "new") {
            if  (b.get('status') !== 'new') {
                return -1
            }
        } else if(b.get('status') === 'new') {
            return 1
        }
        for(var index = 0;index < this.sortedFields.length;index++) {
            if (a.get(this.sortedFields[index][0]) === b.get(this.sortedFields[index][0])) {
                continue
            } else if (this.sortedFields[index][1]) {
                return (a.get(this.sortedFields[index][0]) < b.get(this.sortedFields[index][0]))?-1:1
            } else {
                return (a.get(this.sortedFields[index][0]) < b.get(this.sortedFields[index][0]))?1:-1
            }
        }
        return 1
      },
      
	  featureFilter: function (feat) {
        if (feat.get('status') === 'new') return true

        var search = this.search?this.search.trim().toLowerCase():""
        if (search && !this.fields.some(function (key) {
            return ('' + feat.get(key)).toLowerCase().indexOf(search) > -1
        })){
            return false
        }
        return true
      },
      
	  showFeature: function(feat) {
        return this.revision && (!this.viewportOnly || feat.inViewport)
      },
	  
      setExtentFeatureSize: function() {
        var vm = this
        var size = 0
        this._featurelist.forEach(function(feat){
            if (feat.inViewport) {
                ++size
            }
        })
        this.extentFeaturesSize = size;
      },
	  
      clipToSelection: function() {
        if (this.selectedFeatures.getLength() === 0) {
            return
        }
        this.clippedFeatures.splice(0,this.clippedFeatures.length)
        for (var index = 0;index < this.features.getLength();index++) {
            if (this.features.item(index).get('status') === 'new') {
                this.clippedFeatures.push(this.features.item(index))
            } else {
                break
            }
        }
        var vm = this
        $.each(this.selectedFeatures.getArray().sort(this.featureOrder), function(index, feat){
            if (feat.get('status') === 'new') {
                //already added in the first step
                return
            }
            vm.clippedFeatures.push(feat)
        })
        if (this.clippedOnly) {
            this.updateFeatureFilter(1,0)
        }
      },
      
	  //filter the loaded features based on report name and fire number
      //called when refresh, input search criteria
      //filterType:
      // 1: clipped bushfire fires
      // 2: search
      updateFeatureFilter: function(filterType, wait) {
        var vm = this
        this._filterType = ((this._filterType === undefined || this._filterType === null)?0:this._filterType) | filterType
        if (!vm._updateFeatureFilter) {
            vm._updateFeatureFilter = debounce(function(){
                if (vm._filterType === 0) return
                //console.log("Filter: " + (((vm._filterType & 2) === 2)?"filterBySearch = true  ":"") + (((vm._filterType & 1) === 1)?"filterBySelected = true":""))
                var list = vm.clippedOnly?vm.clippedFeatures:vm.features.getArray()
                if (((vm._filterType & 2) === 2) && vm.hasFeatureFilter) {
                    list = list.filter(vm.featureFilter)
                }
                vm._featurelist.clear()
                vm._featurelist.extend(list)
                vm._filterType = 0
                vm.setExtentFeatureSize()
                if (vm.selectedFeatures.getLength() > 0) {
                    if (list.length === 0) {
                        vm.selectedFeatures.clear()
                    } else {
                        for(var index = vm.selectedFeatures.getLength() - 1;index >= 0;index--) {
                            if (!list.find(function(f){return f === vm.selectedFeatures.item(index)})) {
                                vm.selectedFeatures.removeAt(index)
                            }
                        }
                    }
                }
                vm.revision += 1;
            }, 500)
        }

        if (wait === 0) {
            vm._updateFeatureFilter.call({wait:1})
        } else if (wait === undefined || wait === null){
            vm._updateFeatureFilter()
        } else {
            vm._updateFeatureFilter.call({wait:wait})
        }
      },
      
	  updateViewport: function(wait) {
        var vm = this
        if (!vm._updateViewport) {
            vm._updateViewport = debounce(function(){
                var viewportExtent = vm.map.extent
                vm.features.forEach(function(feat) {
                    feat.inViewport = ol.extent.containsCoordinate(viewportExtent, vm.originpointCoordinate(feat))
                })
                vm.setExtentFeatureSize()
                if (vm.viewportOnly) {
                    vm.revision += 1;
                }
            }, 500)
        }
        if (wait === 0) {
            vm._updateViewport.call({wait:1})
        } else if (wait === undefined || wait === null){
            vm._updateViewport()
        } else {
            vm._updateViewport.call({wait:wait})
        }
      },
      
	  scrollToSelected: function() {
        if (this.selectedFeatures.getLength() === 0) return
        var index = -1

        for (var i = 0;i < this._featurelist.getLength() ;i++) {
            if (this.showFeature(this._featurelist.item(i))) {
                index += 1
                if (this._featurelist.item(i) === this.selectedFeatures.item(0)) {
                    break
                }
            }
        }
        if (index >= 0) {
            var listElement = document.getElementById("bfrs-list")
            if (index < listElement.children.length) {
                listElement.scrollTop += listElement.children[index].getBoundingClientRect().top - listElement.getBoundingClientRect().top
            }
        }
      },
      
	  selectDefaultGeometry: function(feature) {
        var geometries = feature.getGeometry().getGeometriesArray()
        if (geometries.length > 1) {
            if (geometries[1].getPolygons().length === 0){
                feature["selectedIndex"] = [0]
            } else {
                feature["selectedIndex"] = [1,0]
            }
        } else if (geometries.length === 0) {
            delete feature["selectedIndex"]
        } else if (geometries[0] instanceof ol.geom.Point){
            feature["selectedIndex"] = [0]
        } else if (geometries[0].getPolygons().length === 0){
            delete feature["selectedIndex"]
        } else {
            feature["selectedIndex"] = [0,0]
        }
      },
      
	  loadUserProfile: function() {
        var vm = this
        vm._bfrsStatus.phaseBegin("load_profile", 20, "Load profile")
        $.ajax({
	    //url: vm.env.bfrsService + "/api/v1/profile/?format=json",
	    url: "/api/profile.json",
            method:"GET",
            dataType:"json",
            success: function (response, stat, xhr) {
                vm.whoami["bushfire"]["profile"] = response
                vm.profileRevision += 1
                if (vm.whoami["bushfire"]["regions"]) {
                    vm.region = vm.whoami["bushfire"]["profile"]["region_id"] || ""
                    vm.district = vm.whoami["bushfire"]["profile"]["district_id"] || ""
                    vm._bfrsStatus.phaseBegin("load_bushfires", 20, "Load bushfires", false, true)
                    vm.updateCQLFilter(0)
                    vm.bushfireLayer.initialLoad = true
                }
                vm._bfrsStatus.phaseEnd("load_profile")
            },
            error: function (xhr,status,message) {
                vm.isFeatureListLoading = false
                alert(xhr.status + " : " + (xhr.responseText || message))
                vm._bfrsStatus.phaseFailed("load_profile","Failed to loading user profile data. status = " + xhr.status + " , message = " + (xhr.responseText || message))
            },
            xhrFields: {
              withCredentials: true
            }
        })
      },

      loadCapturemethods: function(callback, failedCallback) {
        var vm = this
        if (vm.whoami["bushfire"]["capturemethods"]) {
            //already loaded
            callback()
            return
        }
        var selectCaptureMethod = function(ev) {
            $("#userdialog-button-true").prop("disabled",false);
            $("#userdialog input[name='other_capturemethod']").prop("disabled",$(ev.target).val() !== vm.whoami["bushfire"]["othermethod_id"].toString())
        }
        $.ajax({
            url: vm.env.bfrsService + "/api/v1/capturemethod/?format=json",
            method:"GET",
            dataType:"json",
            success: function (response, stat, xhr) {
                vm.whoami["bushfire"]["capturemethods"] = response
                dialogmessages = []
                othermessage = null
                headermessage = [
                    ["",1],
                    ["Code",3,{"class":"header"}],
                    ["Desc",8,{"class":"header"}]
                ]
                dialogmessages.push(headermessage)
                $.each(vm.whoami["bushfire"]["capturemethods"],function(index,method){
                    dialogmessage = []
                    dialogmessage.push([method["id"],1,{"type":"radio","name":"capturemethod","disabled":false,"click":selectCaptureMethod}])
                    if (method["code"] === "999") {
                        vm.whoami["bushfire"]["other_capturemethod_id"] = method["id"]
                        dialogmessage.push(["Other",3])
                        dialogmessage.push(["",8,{"type":"text","name":"other_capturemethod","disabled":true}])
                        othermessage = dialogmessage
                    } else {
                        dialogmessage.push([method["code"],3])
                        dialogmessage.push([method["desc"],8])
                        dialogmessages.push(dialogmessage)
                    }
                })
                if (othermessage) {
                    dialogmessages.push(othermessage)
                    vm.whoami["bushfire"]["othermethod_id"] = othermessage[0][0]
                }
                vm.whoami["bushfire"]["capturemethod_dialogmessage"] = dialogmessages
                callback()

            },
            error: function (xhr,status,message) {
                failedCallback(xhr.status + " : " + (xhr.responseText || message))
            },
            xhrFields: {
              withCredentials: true
            }
        })
      },

      loadRegions: function() {
        var vm = this
        vm._bfrsStatus.phaseBegin("load_regions",20,"Load regions")
        $.ajax({
            //url: vm.env.bfrsService + "/api/v1/region/?format=json",
 	    url: "/api/brfs-region.json",
            method:"GET",
            dataType:"json",
            success: function (response, stat, xhr) {
                vm.whoami["bushfire"]["regions"] = response
                vm.profileRevision += 1
                if (vm.whoami["bushfire"]["profile"]) {
                    vm.region = vm.whoami["bushfire"]["profile"]["region_id"] || ""
                    vm.district = vm.whoami["bushfire"]["profile"]["district_id"] || ""
                    vm._bfrsStatus.phaseBegin("load_bushfires",20,"Load bushfires",false,true)
                    vm.updateCQLFilter(0)
                    vm.bushfireLayer.initialLoad = true
                }
                vm._bfrsStatus.phaseEnd("load_regions")
            },
            error: function (xhr,status,message) {
                vm.isFeatureListLoading = false
                alert(xhr.status + " : " + (xhr.responseText || message))
                vm._bfrsStatus.phaseFailed("load_regions","Failed to loading regions data. status = " + xhr.status + " , message = " + (xhr.responseText || message))
            },
            xhrFields: {
              withCredentials: true
            }
        })
      },
      loadBfrsStatus: function(features) {
            var vm = this;
            if (features.getLength() > 0) {
                $.ajax({
                    url: "/api/load_bfrs_status.json",
                    method: "GET",
                    dataType: "json",
                    success: (response, stat, xhr) => {
                        if (response.bfrs_list && response.bfrs_list.length > 0) {
                            let bfrsList = response.bfrs_list;

                            bfrsList.forEach(bfrsItem => {
                                let fireNumber = bfrsItem.bfrs;
                                
                                // Check if feature already exists
                                let existingFeature = vm.features.getArray().find(f => f.get("fire_number") === fireNumber);

                                if (fireNumber.startsWith("New bushfire") && !existingFeature) {
                                    // Create new feature
                                    var imported_feature = this.$root.geojson.readFeatures(bfrsItem.feature)[0];
                                    
                                    if (!imported_feature) {
                                        console.log("No feature found in the imported data for fire number: " + fireNumber);
                                        return; 
                                    }
                                    imported_feature = vm.newFeature(imported_feature)
                                    imported_feature.set("fire_number", fireNumber);
                                    imported_feature.set("status", "in_queue");
                                    imported_feature.set("original_status", "new");

                                    var target_feature = imported_feature;
                                    target_feature.imported_feature = imported_feature;

                                    if (bfrsItem.tasks) {
                                        var tasks = JSON.parse(bfrsItem.tasks);
                                        Vue.set(target_feature, 'spatial_data', JSON.parse(bfrsItem.spatial_data));
                                        var allTasks = this.featureTasks(target_feature);
                                        if (!allTasks || allTasks.length === 0){
                                            this._taskManager.initTasks(target_feature);
                                        }
                                        tasks.forEach(task => {
                                            var progress = null;
                                            if (task.status === -1) {
                                                progress = utils.FAILED;
                                            } else if (task.status === -2) {
                                                progress = utils.FAIL_CONFIRMED;
                                            } else if (task.status === 1) {
                                                progress = utils.WAITING;
                                            } else if (task.status === 2) {
                                                progress = utils.RUNNING;
                                            } else if (task.status === 3) {
                                                progress = utils.SUCCEED;
                                            } else if (task.status === 4) {
                                                progress = utils.WARNING;
                                            } else if (task.status === 5) {
                                                progress = utils.IGNORED;
                                            } else if (task.status === 6) {
                                                progress = utils.MERGED;
                                            }

                                            var taskCheck = allTasks && allTasks.find(targetTask => targetTask.taskId === task.taskId);
                                            if (!taskCheck) {
                                                var newTask = this._taskManager.addTask(target_feature, task.scope, task.taskId, task.description, progress);
                                                if(task.status === -1){
                                                    newTask.setStatus(utils.FAILED, task.message);
                                                }
                                            }
                                        });
                                    }
                                    

                                } else if (existingFeature) {
                                    // Existing feature
                                    var imported_feature = this.$root.geojson.readFeatures(bfrsItem.feature)[0];
                                    if (!imported_feature) {
                                        console.log("No feature found in the imported data for fire number: " + fireNumber);
                                        return; 
                                    }
                                    existingFeature.set("original_status", imported_feature.get("status"));
                                    existingFeature.set("status", "in_queue");

                                    var target_feature = vm.featurelist.find(f => f.get('fire_number') === fireNumber) || existingFeature;
                                    if (!target_feature) {
                                        return;
                                    }
                                    target_feature.imported_feature = imported_feature;

                                    if (bfrsItem.tasks) {
                                        var tasks = JSON.parse(bfrsItem.tasks);
                                        Vue.set(target_feature, 'spatial_data', JSON.parse(bfrsItem.spatial_data));
                                        var allTasks = this.featureTasks(target_feature);
                                        if (!allTasks || allTasks.length === 0){
                                            this._taskManager.initTasks(target_feature);
                                        }
                                        tasks.forEach(task => {
                                            var progress = null;
                                            if (task.status === -1) {
                                                progress = utils.FAILED;
                                            } else if (task.status === -2) {
                                                progress = utils.FAIL_CONFIRMED;
                                            } else if (task.status === 1) {
                                                progress = utils.WAITING;
                                            } else if (task.status === 2) {
                                                progress = utils.RUNNING;
                                            } else if (task.status === 3) {
                                                progress = utils.SUCCEED;
                                            } else if (task.status === 4) {
                                                progress = utils.WARNING;
                                            } else if (task.status === 5) {
                                                progress = utils.IGNORED;
                                            } else if (task.status === 6) {
                                                progress = utils.MERGED;
                                            }

                                            var taskCheck = allTasks && allTasks.find(targetTask => targetTask.taskId === task.taskId);
                                            if (!taskCheck) {
                                                var newTask = this._taskManager.addTask(target_feature, task.scope, task.taskId, task.description, progress);
                                                if(task.status === -1){
                                                    newTask.setStatus(utils.FAILED, task.message);
                                                }
                                            }
                                        });
                                    }
                                }
                            });
                        }
                    },
                    error: function (xhr, status, message) {
                        console.log("Error in loading Bfrs status");
                    },
                });
            }
        },
    
      setup: function() {
        var vm = this
        //restore the selected features
        this.annotations.restoreSelectedFeatures()

        // enable resource bfrs layer, if disabled
        if (!this.bushfireMapLayer) {
          // avoid an initial unfiltered WFS load; query only after the BFRS filter is applied
          this.bushfireLayer.initialLoad = false
          this.catalogue.onLayerChange(this.bushfireLayer, true)
        } else if (this.active.isHidden(this.bushfireMapLayer)) {
            this.active.toggleHidden(this.bushfireMapLayer)
        }

        this.annotations.selectable.push(this.bushfireMapLayer)
        this.info.hoverable.push(this.bushfireMapLayer)
        this.annotations.setTool()

        //add feature to place an point based on coordinate
        this.$root.search.setSearchPointFunc(function(searchMethod, coords, name){
            if (["DMS", "MGA"].indexOf(searchMethod) < 0) {
                return false
            }
            if (vm.annotations.tool && vm.annotations.tool.name === "Bfrs Edit Geometry") {
                var feat = vm.selectedFeatures.getLength() === 1?vm.selectedFeatures.item(0):null
                if (!feat) {return false}
                if (!vm.isModifiable(feat)) {
                    alert("Can't modify " + feat.get('status') + " report")
                    return true
                }

                var hasPoint = feat.getGeometry().getGeometriesArray().length > 0 && feat.getGeometry().getGeometriesArray()[0] instanceof ol.geom.Point

                if (hasPoint) {
                    feat.getGeometry().getGeometriesArray()[0] = new ol.geom.Point(coords)
                } else {
                    feat.getGeometry().getGeometriesArray().splice(0,0,new ol.geom.Point(coords))
                }
                feat.getGeometry().setGeometriesArray(feat.getGeometry().getGeometriesArray())
                vm.postModified(feat,1)

                feat.getGeometry().changed()

                return true
            } else if (vm.annotations.tool && vm.annotations.tool.name === "Bfrs Origin Point") {
                var feat = vm.newFeature()
                feat.getGeometry().getGeometriesArray().splice(0,0,new ol.geom.Point(coords))
                feat.getGeometry().setGeometriesArray(feat.getGeometry().getGeometriesArray())
                feat.getGeometry().changed()
                vm.selectedFeatures.clear()
                vm.selectedFeatures.push(feat)
                vm.annotations.setTool("Bfrs Edit Geometry")
                vm.postModified(feat,1)
                return true
            }
        })

        this.$nextTick(this.adjustHeight)
      },
      teardown:function() {
        this.annotations.selectable.splice(0, this.annotations.selectable.length)
      }
    },
    ready: function () {
      var vm = this
      
      this._download_cql_filter = ""
      this._changingDate = false
      this._statusFilters = {
        all_reports: ["fire_not_found=0","fire_not_found='No'"],
        initial_fire_report: ["(report_status=1) and (fire_not_found=0)","(report_status='Initial Fire Report') and (fire_not_found='No')"],
        notification_submitted: ["(report_status=2) and (fire_not_found=0)","(report_status='Notifications Submitted') and (fire_not_found='No')"],
        report_authorised: ["(report_status in (3,4)) and (fire_not_found=0)","(report_status in ('Report Authorised','Reviewed')) and (fire_not_found='No')"],
        fire_not_found: ["fire_not_found=1","fire_not_found='Yes'"]
      }

      this._featurelist = new ol.Collection()
      this._taskManager = utils.getFeatureTaskManager(function() {
        vm.revision++
      })
      vm.taskDialog = new Foundation.Reveal($('#progressInfo'));
      
      //init datepicker
      $('#bfrsStartDate').fdatepicker({
		format: 'yyyy-mm-dd hh:ii',
		disableDblClickSelection: true,
		leftArrow:'<<',
		rightArrow:'>>',
        startDate:null,
        endDate:null,
        pickTime:true,
        minuteStep:1
      });
      try {
          this._startDatePicker = $("#bfrsStartDate").data().datepicker
      } catch(ex) {
          this._startDatePicker = null
      }

      $('#bfrsEndDate').fdatepicker({
		format: 'yyyy-mm-dd hh:ii',
		disableDblClickSelection: true,
		leftArrow:'<<',
		rightArrow:'>>',
        startDate:null,
        endDate:null,
        pickTime:true,
        minuteStep:1
      });

      try {
          this._endDatePicker = $("#bfrsEndDate").data().datepicker
      } catch(ex) {
          this._endDatePicker = null
      }

      vm._bfrsStatus = this.loading.register("bfrs", "Bushfire Report Component")
      vm._bfrsStatus.phaseBegin("initialize", 10, "Initialize")
      var map = this.$root.map

      vm._reportStatus = {
       99999: "unknown",
       99998: "new",
        1: "initial",
        2: "draft_final",
        3: "final_authorised",
        4: "reviewed",
        100:"merged"
      }
      vm._reportStatusName = {
       99999: "Unknown",
       99998: "New Draft Incident",
        1: "Draft Incident",
        2: "Incident Submitted",
        3: "Report Authorised",
        4: "Report Reviewed",
        100:"Report Merged"
      }

      vm.whoami["bushfire"] = vm.whoami["bushfire"] || {}
      vm.whoami["bushfire"]["permission"] = vm.whoami["bushfire"]["permission"] || {
          "create":null,
          "new.edit":false,
          "new.modify":true,
          "new.delete":true,
          "unknown.edit":false,
          "unknown.modify":false,
          "unknown.delete":false,
          "initial.edit":true,
          "initial.modify":null,
          "initial.delete":false,
          "merged.edit":true,
          "merged.modify":false,
          "merged.delete":false,
          "draft_final.edit":true,
          "draft_final.modify":null,
          "draft_final.delete":false,
          "final_authorised.edit":true,
          "final_authorised.modify":null,
          "final_authorised.delete":false,
          "reviewed.edit":true,
          "reviewed.modify":null,
          "reviewed.delete":false,
          "_checked_":0
      }

      var permissionConfig = [
          ["create", vm.createUrl(), "GET", null, function(hasPermission){
             if (hasPermission) {
                 if (vm.tools && !vm.tools.find(function(t){return t === vm.ui.originPointTool})) {
                  vm.tools.push(vm.ui.originPointTool)
                 }
             }
          }],
          ["initial.edit", vm.editUrl, "GET", function(f){return f.get('status') === "initial"}, null],
          ["initial.modify", vm.saveUrl, "PATCH", function(f){return f.get('status') === "initial"}, null],
          ["draft_final.edit", vm.editUrl, "GET", function(f) {return f.get('status') === "draft_final"}, null],
          ["draft_final.modify", vm.saveUrl, "PATCH", function(f) {return f.get('status') === "draft_final"}, null],
          ["final_authorised.edit", vm.editUrl, "GET", function(f) {return f.get('status') === "final_authorised"}, null],
          ["final_authorised.modify", vm.saveUrl, "PATCH", function(f) {return f.get('status') === "final_authorised"}, null],
          ["reviewed.edit", vm.editUrl,"GET", function(f) {return f.get('status') === "reviewed"}, null],
          ["reviewed.modify", vm.saveUrl,"PATCH", function(f) {return f.get('status') === "reviewed"}, null],
          ["merged.edit", vm.editUrl,"GET", function(f){return f.get('status') === "merged"}, null],
      ]
      vm._checkPermission = function(features, callback){
          if (vm.whoami['bushfire']['permission']['_checked_'] === permissionConfig.length) {
              //All permission checks are done
              if (callback) callback()
              return
          }

          var taskCounter = 0

          vm._checkPermissionCallback = vm._checkPermissionCallback || function(callback) {
              if (vm.whoami['bushfire']["permission"]["changed"]) {
                  delete vm.whoami['bushfire']["permission"]["changed"]
                  vm.revision += 1
              }
              if (callback) callback()
          }

          taskCounter += 1
          for (var index = 0;index < permissionConfig.length;index++) {
              var p = permissionConfig[index]
              var url = null
              if (vm.whoami['bushfire']["permission"][p[0]] === null || vm.whoami['bushfire']["permission"][p[0]] === undefined){
                  if (p[1] === null) {
                      //always have the permission
                      vm.whoami['bushfire']["permission"][p[0]] = true
                      vm.whoami['bushfire']["permission"]["changed"] = true
                      vm.whoami['bushfire']['permission']['_checked_'] = vm.whoami['bushfire']['permission']['_checked_'] + 1
                  } else {
                      if (typeof p[1] === "string") {
                          //url is a constant string
                          url = p[1]
                      } else {
                          //url is a function with a bushfire argument.
                          var f = (Array.isArray(features))?features.find(p[3]):(p[3](features)?features:null)
                          if (f) {
                              //get the test url
                              url = p[1](f)
                          } else {
                              //can't find a bushfire to test
                              url = null
                              vm.whoami['bushfire']["permission"][p[0]] = null
                          }
                      }
                  }
              }
              if (url) {
                  taskCounter += 1

                  vm.utils.checkPermission(url,p[2],function(hasPermission,permission){
                      vm.whoami['bushfire']['permission']['_checked_'] = vm.whoami['bushfire']['permission']['_checked_'] + 1
                      vm.whoami['bushfire']["permission"][permission[0]] = hasPermission
                      vm.whoami['bushfire']["permission"]["changed"] = true
                      if (permission[4]) {
                          permission[4](hasPermission)
                      }
                      if (--taskCounter <= 0) vm._checkPermissionCallback(callback)
                  },p)
              }
          }
          if (--taskCounter <= 0) vm._checkPermissionCallback(callback)
      }

      vm.loadRegions()
      vm.ui = {}
      var toolConfig = {features:vm.features, selectedFeatures:vm.selectedFeatures, mapLayers:function(layer){return layer.get("id") === vm.env.bushfireListLayer}}
      /*
      vm.ui.translateInter = vm.annotations.translateInterFactory()(toolConfig)
      vm.ui.translateInter.on("translateend",function(ev){
          vm.postModified(ev.features.getArray())
      })
      */
      vm.ui.dragSelectInter = vm.annotations.dragSelectInterFactory({
        listeners: {
            selected:function(selectedFeatures) {
                vm.scrollToSelected()
            }
        }
      })(toolConfig)
      vm.ui.polygonSelectInter = vm.annotations.polygonSelectInterFactory({
        listeners: {
            selected:function(selectedFeatures) {
                vm.scrollToSelected()
            }
        }
      })(toolConfig)
      vm.ui.selectInter = vm.annotations.selectInterFactory({
        listeners: {
            selected:function(selectedFeatures) {
                vm.scrollToSelected()
            }
        }
      })(toolConfig)
      vm.ui.geometrySelectInter = vm.annotations.selectInterFactory({
        condition: function(event) {
            var result = ol.events.condition.singleClick(event)
            if (result) {
                if (vm.bushfireMapLayer && vm.selectedFeatures.getLength() === 1) {
                    result = vm.bushfireMapLayer.getSource().getFeaturesAtCoordinate(event.coordinate).findIndex(function(o) {return o === vm.selectedFeatures.item(0)}) >= 0
                } else {
                    result = false
                }
            }
            return result
        }
      })($.extend({selectMode:"geometry"},toolConfig))

      vm.ui.modifyInter = vm.annotations.modifyInterFactory()({features:vm.selectedFeatures,mapLayers:function(layer){return layer.get("id") === vm.env.bushfireListLayer }})
      vm.ui.modifyInter.on("featuresmodified",function(ev){
          if (ev.features.getLength() === 1 ) {
            vm.validateBushfire(ev.features.item(0),"modifyBushfire")
          }
          vm.postModified(ev.features.getArray(),-1)
      })

      vm.ui.originPointDraw = vm.annotations.pointDrawFactory({
        events: {
            addfeaturegeometry:true
        },
        drawOptions:{
        }
      })({
        features:vm.drawings
      })

      var canDrawFireboundary = function(ev) {
        var feat = (vm.selectedFeatures.getLength() == 1)?vm.selectedFeatures.item(0):null
        if (feat) {
            var featGeometry = feat.getGeometry()
            if (vm.isModifiable(feat) && vm.isFireboundaryDrawable(feat)) {
                if (vm.bushfireMapLayer) {
                    if (vm.ui.fireboundaryDraw.drawing) {
                        return true
                    } else {
                        return vm.bushfireMapLayer.getSource().getFeaturesAtCoordinate(ev.coordinate).findIndex(function(o) {return o === feat}) < 0
                    }
                } else {
                    return false
                }
            } else {
                return false
            }
        } else {
            //alert("Plase choose a bushfire to draw a fire boundary.")
            return false
        }
      }

      vm.ui.fireboundaryDraw = vm.annotations.polygonDrawFactory({
        events: {
            addfeaturegeometry:true
        },
        listeners:{
            drawstart: function() {
                $.each(vm.ui.modifyTool.interactions,function(index,interaction) {
                    if (interaction !== vm.ui.fireboundaryDraw) {
                        interaction.setActive(false)
                    }
                })
            },
            drawend: function() {
                $.each(vm.ui.modifyTool.interactions,function(index,interaction) {
                    if (interaction !== vm.ui.fireboundaryDraw) {
                        interaction.setActive(true)
                    }
                })
            },
        },
        drawOptions:{
            freehandCondition:function(ev) {
                var result = ol.events.condition.shiftKeyOnly(ev)
                if (result) {
                    return canDrawFireboundary(ev)
                }
                return result
            },
            condition:function(ev) {
                var result = ol.events.condition.noModifierKeys(ev)
                if (result) {
                    return canDrawFireboundary(ev)
                }
                return result
            }
        },
        drawProperties:{
            minDistance:20,
            freehandSnapTolerance:12,
        }
      })({
        features:vm.drawings
      })
      vm.drawings.on("add",function(ev){
        if (vm.annotations.tool.name === "Bfrs Edit Geometry") {
            if (vm.selectedFeatures.getLength() === 1){
                var f = vm.selectedFeatures.item(0)
                var indexes = null

                var index = f.getGeometry().getGeometriesArray().findIndex(function(g){return g instanceof ol.geom.MultiPolygon})
                if (index >= 0) {
                    indexes = [index,f.getGeometry().getGeometriesArray()[index].getPolygons().length]
                    f.getGeometry().getGeometriesArray()[index].appendPolygon(ev.element.getGeometry())
                } else {
                    index = f.getGeometry().getGeometriesArray().length
                    indexes = [index,0]
                    f.getGeometry().getGeometriesArray().push(new ol.geom.MultiPolygon([ev.element.getGeometry().getCoordinates()]))
                }
                f.getGeometry().setGeometriesArray(f.getGeometry().getGeometriesArray())
                f.getGeometry().changed()
                vm.postModified(f,2)
                vm.validateBushfire(f,"addFireboundary")

                vm.ui.fireboundaryDraw.dispatchEvent(vm.map.createEvent(vm.ui.fireboundaryDraw,"addfeaturegeometry",{feature:f,indexes:indexes}))
            }
        } else {
            var f = null
            var selectedFeat = (vm.selectedFeatures.getLength() === 1)?vm.selectedFeatures.item(0):null
            if (selectedFeat && selectedFeat.get('status') === 'new' && !selectedFeat.getGeometry().getGeometriesArray().find(function(g) {return g instanceof ol.geom.Point})) {
                f = selectedFeat
                f.getGeometry().getGeometriesArray().splice(0,0,ev.element.getGeometry())
                f.getGeometry().setGeometriesArray(f.getGeometry().getGeometriesArray())
                f.getGeometry().changed()
            } else {
                f = vm.newFeature()
                f.getGeometry().getGeometriesArray().splice(0,0,ev.element.getGeometry())
                f.getGeometry().setGeometriesArray(f.getGeometry().getGeometriesArray())
                f.getGeometry().changed()
                vm.selectedFeatures.clear()
                vm.selectedFeatures.push(f)
                vm.annotations.setTool("Bfrs Edit Geometry")
                vm.scrollToSelected()
            }
            vm.postModified(f,1)
            //vm.validateBushfire(f,"addOriginPoint")

            vm.ui.originPointDraw.dispatchEvent(vm.map.createEvent(vm.ui.originPointDraw,"addfeaturegeometry",{feature:f,indexes:[0]}))
        }
        vm.drawings.clear()
      })

      //add tools
      var tools = [
          {
              name: 'Bfrs Select',
              label: 'Select',
              icon: 'fa-mouse-pointer',
              scope:["bfrs"],
              keepSelection:true,
              interactions: [
                  vm.ui.dragSelectInter,
                  vm.ui.polygonSelectInter,
                  vm.ui.selectInter,
                  //vm.ui.translateInter,
                  vm.annotations.keyboardInterFactory({
                    selectEnabled:false,
                    events: {
                        deleteallgeometries:true
                    },
                    deleteSelected:function(features,selectedFeatures) {
                        var feature = null
                        for(i = selectedFeatures.getLength() - 1;i >= 0;i--) {
                            feature = selectedFeatures.item(i)
                            if (vm.isDeletable(feature)) {
                                vm.deleteFeature(feature)
                            } else {
                                alert("Can't delete a existing bushfire.")
                            }
                        }
                    }
                  }),
              ],
              keepSelection:true,
              onSet: function() {
                  vm.ui.dragSelectInter.setMulti(true)
                  vm.ui.selectInter.setMulti(true)
              },
              /*
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Select bushfires using keyboard or mouse",
                    ]
                }
              ]
              */
          },{
              name: 'Bfrs Edit Geometry',
              label: 'Edit Geometry',
              icon: 'fa-pencil',
              scope:[],
              interactions: [
                  vm.ui.geometrySelectInter,
                  vm.annotations.keyboardInterFactory({
                    selectEnabled:false,
                    events:{
                        deletefeaturegeometry:true
                    },
                    deleteSelected:function(features,selectedFeatures) {
                        selectedFeatures.forEach(function (feature) {
                            if (vm.isModifiable(feature) && feature["selectedIndex"] !== undefined) {
                                var geom = vm.annotations.getSelectedGeometry(feature)
                                if (geom instanceof ol.geom.Point) {
                                    if (feature.get('status') === "new") {
                                        vm.deleteFeature(feature)
                                    } else {
                                        alert("Can't delete existing bushfire's orgin point.")
                                    }
                                    return
                                }
                                vm.annotations.deleteSelectedGeometry(feature,this)
                                vm.selectDefaultGeometry(feature)
                                vm.postModified(feature,2)
                                vm.validateBushfire(feature,"deleteFireboundary")
                            }
                        },this)
                    }
                  }),
                  vm.ui.modifyInter,
                  this.ui.fireboundaryDraw
              ],
              selectMode:"geometry",
              keepSelection:true,
              onUnset: function() {
                  vm.selectedFeatures.forEach(function(f){
                      f.getGeometry().changed()
                  })
              },
              onSet: function() {
                  vm.ui.geometrySelectInter.setMulti(false)
                  if (vm.selectedFeatures.getLength() > 1) {
                      vm.selectedFeatures.clear()
                  } else if (vm.selectedFeatures.getLength() == 1) {
                    var selectedFeature = vm.selectedFeatures.item(0)
                    if (selectedFeature["selectedIndex"] === undefined ) {
                        vm.selectDefaultGeometry(selectedFeature)
                    }
                    var currentScale = vm.map.getScale()
                 }
              },
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Click on the map to start drawing a bushfire",
                        "Hold down the 'SHIFT' key during drawing to enable freehand mode",
                        "To delete a fire boundary click inside the fire boundary to be deleted and press the 'DELETE' key",
                        "To modify the boundary or origin click and drag to adjust"
                    ]
                }
              ]
          },{
              name: 'Bfrs Origin Point',
              label: 'Add Bushfire',
              icon: '/static/dist/static/symbols/fire/origin.svg',
              tints: vm.tints,
              selectedFillColour:[0, 0, 0, 0.25],
              fillColour:[0, 0, 0, 0.25],
              labelStyle:{
                offsetX:17,
                strokeWidth:8,
                font: "Bold 12px Helvetica,Roboto,Arial,sans-serif"
              },
              size:2,
              interactions: [
                  vm.ui.originPointDraw
              ],
              sketchStyle: vm.annotations.getIconStyleFunction(vm.tints),
              scope:[],
              measureLength:false,
              measureArea:false,
              keepSelection:true,
              showName: true,
              getMeasureGeometry:function() {
                if (vm.isFireboundaryDrawable(this)) {
                    return this.getGeometry()
                } else {
                    return null
                }
              },
              onSet: function() {
                  /*
                  if (vm.selectedFeatures.getLength() > 1) {
                      vm.selectedFeatures.clear()
                  } else {
                      var currentScale = vm.map.getScale()
                  }
                  */
              },
              comments:[
                {
                    name:"Tips",
                    description:[
                        "Click on the map or search a point to create a new bushfire in SSS."
                    ]
                }
              ]
          }
      ]

      tools.forEach(function (tool) {
        vm.annotations.tools.push(tool)
      })

      vm.ui.modifyTool = vm.annotations.tools.find(function(tool){return tool.name === "Bfrs Edit Geometry"})
      vm.ui.originPointTool = vm.annotations.tools.find(function(tool){return tool.name === "Bfrs Origin Point"})
      vm.ui.panTool = vm.annotations.tools.find(function(tool){return tool.name === "Pan"})
      vm.ui.selectTool = vm.annotations.tools.find(function(tool){return tool.name === "Bfrs Select"})

      this.$root.fixedLayers.push({
        type: 'WFSLayer',
        name: 'Bushfire Report',
        id: vm.env.bushfireListLayer,
        getFeatureInfo: function (f) {
            return {name: f.get("fire_number"), img: map.getBlob(f, ['icon', 'tint']), comments: f.get('name') + "(" + (vm._reportStatusName[f.get('report_status')] || vm._reportStatusName[99999]) + ")"}
        },
        initialLoad: false,
        refresh: 300,
        features: vm._featurelist,
        min_interval: 60,
        max_interval: 600,
        interval_step: 60,
        dependentLayers: [
            {
                type: 'TileLayer',
                name: 'Fire Boundary of Bushfire Final Report',
                id: vm.env.bushfireFinalFireBoundaryLatestLayer,
                autoAdd:false,
                inheritRefresh: true
            },
            {
                type: 'ImageLayer',
                name: 'Fire Boundary of Selected Bushfire Final Report',
                id: vm.env.bushfireFinalFireBoundaryLatestLayer,
                // style: getLayerId(this.env.bushfireFinalFireBoundaryLatestLayer) + ".selected",
                mapLayerId:vm.env.bushfireFinalFireBoundaryLatestLayer + "_selected",
                autoAdd:false,
                inheritRefresh: true
            }
        ],
        /*
        getUpdatedTime:function(features) {
            var updatedTime = null
            $.each(features,function(index,f){
                if (f.get('status') !== 'new') {
                    var featureModifiedDate = moment(new Date(f.get('modified')))
                    if (updatedTime === null) {
                        updatedTime =  featureModifiedDate
                    } else if(updatedTime < featureModifiedDate) {
                        updatedTime =  featureModifiedDate
                    }
                }
            })
            return updatedTime
        },
        */
        onerror: function(status, message) {
            vm.isFeatureListLoading = false
            vm._bfrsStatus.phaseFailed("load_bushfires", status + " : " + message)
        },
        onload: function(loadType, vectorSource, features, defaultOnload) {
            //combine the two spatial columns into one
            $.each(features, function(index, feature) {
                //console.log("BUSHFIRE FEATURES");
                //console.log(feature);
                vm.initBushfire(feature)
            })

            function processResources() {
                // merge the current changes with the new features
                var insertPosition = 0
                var loadedFeature = null;

                for (var index = vm.features.getLength() - 1; index >= 0; index--) {
                    f = vm.features.item(index)
                    if (f.get('status') === 'new') {
                        //new features always are the begining and sorted.
                        if (f.get('sss_id')) {
                            //save before (PWM:saved?)
                            loadedFeature = features.find(function(f2){
                                return f.get('sss_id') === f2.get('sss_id')
                            })
                            if (!loadedFeature) {                                
                                //still not save, keep the current new bushfire (PWM: saved?)
                                features.splice(insertPosition, 0, f)
                                insertPosition += 1
                            } else{
                                if (f.get('tint') === 'modified'){
                                    //feature was changed after saving
                                    //replace the loadedFeature's geometry with the modified version
                                    loadedFeature.setGeometry(f.getGeometry())
                                    loadedFeature.set('tint','modified',true)
                                    loadedFeature.set('fillColour',vm.tints[loadedFeature.get('tint') + ".fillColour"],true)
                                    loadedFeature.set('colour',vm.tints[loadedFeature.get('tint') + ".colour"],true)
                                    loadedFeature.set('modifyType',f.get('modifyType'),true)
                                } else {
                                    //already saved into the database, and not change after saving, ignore it
                                }
                                if (f.tasks && f.tasks.length > 0) {
                                    loadedFeature.tasks = f.tasks
                                }
                                var i = vm.selectedFeatures.getArray().findIndex(function(o) {return o.get('fire_number') === f.get('fire_number')})
                                if (i >= 0) {
                                    vm.selectedFeatures.removeAt(i)
                                    vm.selectedFeatures.push(loadedFeature)
                                }
                            }
                        } else {
                            //not save before
                            features.splice(insertPosition,0,f)
                            insertPosition += 1
                        }
                    } else if (f.get('tint') === 'modified' || f.tasks) {
                        loadedFeature = features.find(function(f2){return f.get('id') === f2.get('id')})
                        if (loadedFeature) {
                            if (f.get('tint') === 'modified') {
                                //replace the loadedFeature's geometry with the modified version
                                loadedFeature.setGeometry(f.getGeometry())
                                loadedFeature.set('tint', 'modified', true)
                                loadedFeature.set('fillColour', vm.tints[loadedFeature.get('tint') + ".fillColour"], true)
                                loadedFeature.set('colour', vm.tints[loadedFeature.get('tint') + ".colour"], true)
                                loadedFeature.set('modifyType', f.get('modifyType'), true)
                                if (f.intersectionPoints) {
                                    loadedFeature.intersectionPoints = f.intersectionPoints
                                }
                            }
                            if (f.tasks && f.tasks.length > 0) {
                                loadedFeature.tasks = f.tasks
                            }
                        }
                    }
                }
                if (vm.selectedFeatures.getLength() > 0) {
                    for(var index = vm.selectedFeatures.getLength() - 1;index >= 0;index--) {
                        var f = vm.selectedFeatures.item(index)
                        loadedFeature = features.find(function(f1){return f1.get('fire_number') === f.get('fire_number')})
                        if (loadedFeature) {
                            if (f.selectedIndex !== undefined) {
                                if (vm.annotations.getSelectedGeometry(loadedFeature, f.selectedIndex)) {
                                    loadedFeature.selectedIndex = f.selectedIndex
                                } else {
                                    vm.selectDefaultGeometry(loadedFeature)
                                }
                            }
                            vm.selectedFeatures.setAt(index, loadedFeature)
                        } else {
                            vm.selectedFeatures.removeAt(index)
                        }
                    }
                }
                if (vm.clippedFeatures.length > 0) {
                    for(var index = vm.clippedFeatures.length - 1;index >= 0;index--) {
                        var f = vm.clippedFeatures[index]
                        loadedFeature = features.find(function(f1){return f1.get('fire_number') === f.get('fire_number')})
                        if (loadedFeature) {
                            vm.clippedFeatures[index] = loadedFeature
                        } else {
                            vm.clippedFeatures.splice(index, 1)
                        }
                    }
                }
                vm.features.clear()
                vm.features.extend(features.sort(vm.featureOrder))	//if commented out, no fires show
                vm.updateViewport(0)	//if commented out, fires still load
                vm.loadBfrsStatus(vm.features)
                vm.updateFeatureFilter(3, 0)
                if (vm.whoami['bushfire']["permission"]["changed"]) {
                    delete vm.whoami['bushfire']["permission"]["changed"]
                    vm.revision += 1
                }
                vm.isFeatureListLoading = false
                vm._bfrsStatus.phaseEnd("load_bushfires")
            }
            vm._checkPermission(features, processResources)
        }
      })
      //this.measure.register("dpaw:bushfirelist_latest",this.features)

      vm._bfrsStatus.phaseEnd("initialize")
      // setInterval(vm.updateBfrsUploadProgress, 30000);
      vm._bfrsStatus.phaseBegin("gk-init", 20, "Listen 'gk-init' event", true, true)
      // post init event hookup
      this.$on('gk-init', function () {
        vm._bfrsStatus.phaseEnd("gk-init")

        vm._bfrsStatus.phaseBegin("attach_event", 10, "Attach events")
        map.olmap.getView().on('propertychange', function() {vm.updateViewport()})

        vm.selectedFeatures.on('add', function (event) {
          if (vm.annotations.tool.selectMode === "geometry") {
              if (event.element["selectedIndex"] === undefined) {
                  vm.selectDefaultGeometry(event.element)
              }
          }
          vm.refreshSelectedFinalFireboundaryLayer()
          //vm.zoomToSelected(200)
        })
        vm.selectedFeatures.on('remove', function (event) {
          vm.refreshSelectedFinalFireboundaryLayer()
          //vm.zoomToSelected(200)
          if (vm.selectedFeatures.getLength() !== 1) {
              if (vm.annotations.tool === vm.ui.modifyTool) {
                  vm.annotations.setTool(vm.ui.panTool)
              }
          }

          //remove the index of the selected geometry in geometry collection
          //delete event.element['selectedIndex']
        })
        // enable resource bfrs layer, if disabled
        //vm.annotations.setDefaultTool('bfrs','Pan')
        $.each([vm.annotations.ui.defaultPan], function(index, t) {
            t.scope = t.scope || []
            t.scope.push("bfrs")
        })

        $.each(vm.annotations.tools.filter(function (t) {
          return t.scope && t.scope.indexOf("bfrs") >= 0
        }), function(index, t){
            vm.tools.splice(index, 0, t)
        })

        vm.map.olmap.on("removeLayer",function(ev){
            if (ev.mapLayer.get('id') === vm.env.bushfireListLayer) {
                vm.features.clear()
                vm._featurelist.clear()
                vm.isFeatureListLoading = false
            }
        })

        vm._resolutionChanged = debounce(function(ev){
            vm.featureLabelDisabled = (vm.map.olmap.getView().getResolution() >= 0.003)
        }, 200)

        vm._resolutionChanged()

        vm.map.olmap.getView().on("change:resolution", function(){
            vm._resolutionChanged()
        })

        vm.selectedFeatures.on('add', function (event) {
            vm.selectRevision += 1
        })
        vm.selectedFeatures.on('remove', function (event) {
            vm.selectRevision += 1
        })

        vm._bfrsStatus.phaseEnd("attach_event")
        //load user profile
        vm.loadUserProfile()
      })
    }
  }
</script>
