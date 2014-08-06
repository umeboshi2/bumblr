define (require, exports, module) ->
  $ = require 'jquery'
  _ = require 'underscore'
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'

  Qs = require 'qs'
  
  ########################################
  # stuff
  ########################################
  baseURL = 'http://api.tumblr.com/v2'

  class TumblrClient
    tagged: (tag, options, callback) ->
      options = options || {}
      options.tag = tag
      @_get 'tagged', options, callback, true

    _get: (path, params, callback, addApiKey) ->
      
  ########################################
  # Models
  ########################################

  class Page extends Backbone.Model
    url: () ->
      pathname = '/bumblr/pages/'
      if window.location.pathname == '/index.local.html'
        pathname = '/pages/'
      return pathname + @id + '.json'

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
      

  class BumblrSettings extends BaseLocalStorageModel

  bumblr_settings = new BumblrSettings id:'bumblr'
  
  MSGBUS.reqres.setHandler 'bumblr:get_app_settings', ->
    bumblr_settings
      
  module.exports =
    Page: Page
    
