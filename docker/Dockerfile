ARG STACTOOLS_VERSION=latest
FROM stacutils/stactools:$STACTOOLS_VERSION

WORKDIR /opt/stactools-worldclim

# For caching purposes, install dependencies but remove the actual package
COPY pyproject.toml setup.cfg ./
COPY src/stactools/worldclim/__init__.py src/stactools/worldclim/
RUN pip install . \
    && rm -r /opt/conda/lib/python3.8/site-packages/stactools/worldclim

COPY src ./src
RUN pip install .
