define (require, exports, module) ->
  $ = require 'jquery'
  _ = require 'underscore'
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'
  PageableCollection = require 'backbone.paginator'
  qs = require 'querystring'
  OAuth = require 'oauth'
    
  ########################################
  # Base Models
  ########################################

  class BaseLocalStorageModel extends Backbone.Model
    initialize: () ->
      @fetch()
      @on 'change', @save, @

    fetch: () ->
      console.log '===== FETCH FIRED LOADING LOCAL STORAGE ===='
      @set JSON.parse localStorage.getItem @id

    save: (attributes) ->
      console.log '===== CHANGE FIRED SAVING LOCAL STORAGE ===='
      localStorage.setItem(@id, JSON.stringify(@toJSON()))

    destroy: (options) ->
      console.log '===== DESTROY LOCAL STORAGE ===='
      localStorage.removeItem @id

    isEmpty: () ->
      _.size @attributes <= 1
      

  ########################################
  # stuff
  ########################################
  baseURL = 'http://api.tumblr.com/v2'

  class TumblrClient
    tagged: (tag, options, callback) ->
      options = options || {}
      options.tag = tag
      @_get '/tagged', options, callback, true

    _get: (path, params, callback, addApiKey) ->
      params = params || {}
      if addApiKey
        params.api_key = @credentials.consumer_key

      $.getJSON baseURL + path + '?callback=?', params, callback
        
        

  ########################################
  # Test Tumblr Models and collections
  ########################################
  #
  class BaseTumblrModel extends Backbone.Model
    baseURL: baseURL
  
  class BlogInfo extends BaseTumblrModel
    url: () ->
      @baseURL + '/blog/' + @id + '/info?api_key=' + @api_key + '&callback=?'

    
  class Post extends BaseTumblrModel

    
  #class LocalBlog extends BaseLocalStorageModel
  #  id: 'bumblr_blogs'
  class LocalBlogModel extends Backbone.Model

    
  class LocalBlogCollection extends Backbone.Collection
    initialize: () ->
      settings = MSGBUS.reqres.request 'bumblr:get_app_settings'
      @api_key = settings.get 'consumer_key'
      @fetch()
      @on 'change', @save, @
      
    fetch: () ->
      console.log '===========fetching local blogs========='
      blogs = JSON.parse(localStorage.getItem('bumblr_blogs')) || []
      @set blogs
      
    save: (collection) ->
      console.log '===========saving local blogs========='
      localStorage.setItem('bumblr_blogs', JSON.stringify(@toJSON()))

    add_blog: (name) ->
      sitename = name + '.tumblr.com'
      model = new BlogInfo
      model.set 'id', sitename
      model.api_key = @api_key
      @add model
      model.fetch()
      

  class PhotoPostCollection extends Backbone.Collection
    url: () ->
      baseURL + '/' + @id + '/posts/photo' + '?callback=?'
      
  ########################################
  # Models
  ########################################

  class Page extends Backbone.Model
    url: () ->
      pathname = '/bumblr/pages/'
      if window.location.pathname == '/index.local.html'
        pathname = '/pages/'
      return pathname + @id + '.json'

  class BumblrSettings extends BaseLocalStorageModel
    id: 'bumblr_settings'

  #bumblr_settings = new BumblrSettings id:'bumblr'
  bumblr_settings = new BumblrSettings
  MSGBUS.reqres.setHandler 'bumblr:get_app_settings', ->
    bumblr_settings
      
  client = new TumblrClient
  settings = MSGBUS.reqres.request 'bumblr:get_app_settings'
  client.credentials = settings.attributes
  MSGBUS.reqres.setHandler 'bumblr:get_tumblr_client', ->
    client
    
  local_blogs = new LocalBlogCollection
  MSGBUS.reqres.setHandler 'bumblr:get_local_blogs', ->
    local_blogs
    
  module.exports =
    Page: Page
    
