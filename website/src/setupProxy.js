const proxy = require('http-proxy-middleware');
require('dotenv').config({ silent: true });

module.exports = function(app) {
	app.use(proxy('/map', { target: 'http://localhost:5000/' }));
};
