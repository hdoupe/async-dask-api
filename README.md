Env setup
```
conda create -y -n tc-dask-demo python=3.6 taxcalc dask tornado -c ospc
source activate tc-dask-demo
pip install gunicorn falcon requests httpie
```

In window 1, run
`source activate tc-dask-demo && python dask_rest_api.py`

In window 2, run
`source activate tc-dask-demo && python mock_pb.py`

In window3, test with:
`source activate tc-dask-demo && http -f POST http://localhost:8888/taxcalc policy='{"2018": {"_II_em": [8000]}}'`
