define (require, exports, module) ->
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'
  Marionette = require 'marionette'

  Templates = require 'demoapp/templates'
  Models = require 'demoapp/models'
  BaseModels = require 'models'
    
  require 'jquery-ui'
  
  class SideBarView extends Backbone.Marionette.ItemView
    template: Templates.sidebar
    events:
      'click .mainview-button': 'mainview_pressed'
      'click .dashboard-view-button': 'dashboard_view_pressed'
      'click .list-blogs-button': 'list_blogs_pressed'
      
    _navigate: (url) ->
      r = new Backbone.Router
      r.navigate url, trigger:true

    mainview_pressed: () ->
      console.log 'mainview_pressed called'
      @_navigate '#demo'
      
    dashboard_view_pressed: () ->
      console.log 'dashboard_view_pressed called'
      @_navigate '#demo/dashboard'

    list_blogs_pressed: () ->
      console.log 'list_blogs_pressed called'
      @_navigate '#demo/listblogs'
      
      
  render_calendar_event = (calEvent, element) ->
    calEvent.url = '#bumblr/viewmeeting/' + calEvent.id
    element.css
      'font-size' : '0.9em'

  calendar_view_render = (view, element) ->
    MSGBUS.commands.execute 'bumblr:maincalendar:set_date'

  loading_calendar_events = (bool) ->
    loading = $ '#loading'
    header = $ '.fc-header'
    if bool
      loading.show()
      header.hide()
    else
      loading.hide()
      header.show()
      

  class SimpleBlogInfoView extends Backbone.Marionette.ItemView
    template: Templates.simple_blog_info

  class SimpleBlogListView extends Backbone.Marionette.CollectionView
    childView: SimpleBlogInfoView
    
                
  class MainBumblrView extends Backbone.Marionette.ItemView
    template: Templates.main_bumblr_view

  class BumblrDashboardView extends Backbone.Marionette.ItemView
    template: Templates.bumblr_dashboard_view
    
  class ShowPageView extends Backbone.Marionette.ItemView
    template: Templates.page_view


  class SimpleBlogPostView extends Backbone.Marionette.ItemView
    template: Templates.simple_post_view
    #tagName: 'span'
    className: 'col-md-4'
    
  class BlogPostListView extends Backbone.Marionette.CollectionView
    childView: SimpleBlogPostView
    className: 'row'

  module.exports =
    SideBarView: SideBarView
    MainBumblrView: MainBumblrView
    BumblrDashboardView: BumblrDashboardView
    SimpleBlogListView: SimpleBlogListView
    BlogPostListView: BlogPostListView
    
    