function init_healthapp() {
  Handlebars.registerHelper('booltostr', function(str) {
    return str ? 'Yes' : 'no';
  });

  function get_servers(callback) {
    $.get('/api/v0/servers', callback);
  }

  function get_server(servername, callback) {
    $.get('/api/v0/status/' + servername, callback);
  }

  function get_alerts(callback) {
    $.get('/api/v0/alerts', callback);
  }

  var server_list = Handlebars.compile($('#server-list-template').html()),
      alert_list = Handlebars.compile($('#alert-list-template').html()),
      flash_template = Handlebars.compile($('#flash-template').html()),
      server_view = Handlebars.compile($('#server-view-template').html()),
      user_pagination_interval = 100,
      $content = $('#content'),
      $flashes = $('#flashes'),
      $title = $('h1'),
      router = new Navigo(null, false, '#!'),
      last_flash = null;

  function flash(type, message) {
    last_flash = {type: type, message: message};
  }

  function render_page(title, contents) {
    $title.text(title);
    $content.html(contents);
    router.updatePageLinks();
    if (last_flash) {
      $flashes.html(flash_template(last_flash));
      last_flash = null;
    } else {
      $flashes.empty();
      last_flash = null;
    }
  };


  function servers_list_page(params) {
    get_servers(function(data) {
      render_page('Servers', server_list(data));
    });
  }

  function server_view_page(params) {
      get_server(params.servername, function(data) {
        render_page(params.servername, server_view({info: data}));
      });
  }

  function alerts_list_page(params) {
    get_alerts(function(data) {
      render_page('Alerts', alert_list(data));
    });
  }

  router.on({
    '/': servers_list_page,
    '/alerts': alerts_list_page,
    '/server/:servername': server_view_page,

  }).resolve();
}
