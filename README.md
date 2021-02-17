# Stocks Pattern Analyzer

- Start `Rest API`
- Start `Dash App`
- Enjoy

## TODOs

- Measure the effect of window transformations
    - MinMax scaling
    - Softmax
    - No transform
- Dockerized service(s)
- Common base class for serializable objects

### Optimizations

- Parallel data download
- Parallel data processing (search tree creation)

## Releasing to Heroku (toy deployment)

First of all, this is a mono-repo which is not ideal, but the deployment is just an example.
This is why a multi-buildpack solution is used with `heroku-community/multi-procfile`.

```bash
$ heroku create stock-restapi --remote restapi
$ heroku buildpacks:add -a stock-restapi heroku/python
$ heroku buildpacks:add -a stock-restapi -i 1 heroku-community/multi-procfile
$ heroku config:set -a stock-restapi PROCFILE=Procfile_restapi
$ git push restapi master
$
$ heroku create stock-dash-client --remote dash
$ heroku buildpacks:add -a stock-dash-client heroku/python
$ heroku buildpacks:add -a stock-dash-client -i 1 heroku-community/multi-procfile
$ heroku config:set -a stock-dash-client PROCFILE=Procfile_dash
$ heroku config:set -a stock-dash-client REST_API_URL=https://stock-restapi.herokuapp.com --> this is the URL where we can reach the RestAPI
$ git push dash master
```

Files:
- `runtime.txt` describes the Python version
- `Procfile_restapi` Heroku Procfile for the RestAPI app 
- `Procfile_dash` Heroku Procfile for the Dash Client app 

## References

- Style from: https://dash-gallery.plotly.host/dash-oil-and-gas/
