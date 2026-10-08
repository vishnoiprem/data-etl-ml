//#region src/reference/v8.json.d.ts
declare const _exports: {
  $version: number;
  $root: {
    version: {
      required: boolean;
      type: string;
      values: number[];
      doc: string;
      example: number;
    };
    name: {
      type: string;
      doc: string;
      example: string;
    };
    metadata: {
      type: string;
      doc: string;
      example: {
        "styleeditor:slimmode": boolean;
        "styleeditor:comment": string;
        "styleeditor:version": string;
        "example:object": {
          String: string;
          Number: number;
          Boolean: boolean;
        };
      };
    };
    center: {
      type: string;
      value: string;
      length: number;
      doc: string;
      example: number[];
    };
    centerAltitude: {
      type: string;
      doc: string;
      example: number;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    zoom: {
      type: string;
      doc: string;
      example: number;
    };
    bearing: {
      type: string;
      default: number;
      period: number;
      units: string;
      doc: string;
      example: number;
    };
    pitch: {
      type: string;
      default: number;
      units: string;
      doc: string;
      example: number;
      "sdk-support": {
        "0-60 degrees": {
          js: string;
          android: string;
          ios: string;
        };
        "0-85 degrees": {
          js: string;
          android: string;
          ios: string;
        };
        "0-180 degrees": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    roll: {
      type: string;
      default: number;
      units: string;
      doc: string;
      example: number;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    state: {
      type: string;
      default: {};
      doc: string;
      example: {
        chargerType: {
          default: string[];
        };
        minPreferredChargingSpeed: {
          default: number;
        };
      };
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    light: {
      type: string;
      doc: string;
      example: {
        anchor: string;
        color: string;
        intensity: number;
      };
    };
    sky: {
      type: string;
      doc: string;
      example: {
        "sky-color": string;
        "sky-horizon-blend": number;
        "horizon-color": string;
        "horizon-fog-blend": number;
        "fog-color": string;
        "fog-ground-blend": number;
        "atmosphere-blend": (string | number | string[])[];
      };
    };
    projection: {
      type: string;
      doc: string;
      example: {
        type: (string | number | string[])[];
      };
    };
    terrain: {
      type: string;
      doc: string;
      example: {
        source: string;
        exaggeration: number;
      };
    };
    sources: {
      required: boolean;
      type: string;
      doc: string;
      example: {
        "maplibre-demotiles": {
          type: string;
          url: string;
        };
        "maplibre-tilejson": {
          type: string;
          url: string;
        };
        "maplibre-streets": {
          type: string;
          tiles: string[];
          maxzoom: number;
        };
        "wms-imagery": {
          type: string;
          tiles: string[];
          tileSize: number;
        };
      };
    };
    sprite: {
      type: string;
      doc: string;
      example: string;
    };
    glyphs: {
      type: string;
      doc: string;
      example: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "omit to use local fonts": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "font-faces": {
      type: string;
      doc: string;
      example: {
        "Noto Sans Regular": {
          url: string;
          "unicode-range": string[];
        }[];
        Unifont: string;
      };
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    transition: {
      type: string;
      doc: string;
      example: {
        duration: number;
        delay: number;
      };
    };
    layers: {
      required: boolean;
      type: string;
      value: string;
      doc: string;
      example: {
        id: string;
        source: string;
        "source-layer": string;
        type: string;
        paint: {
          "line-color": string;
        };
      }[];
    };
  };
  sources: {
    "*": {
      type: string;
      doc: string;
    };
  };
  source: string[];
  source_vector: {
    type: {
      required: boolean;
      type: string;
      values: {
        vector: {
          doc: string;
        };
      };
      doc: string;
    };
    url: {
      type: string;
      doc: string;
    };
    tiles: {
      type: string;
      value: string;
      doc: string;
    };
    bounds: {
      type: string;
      value: string;
      length: number;
      default: number[];
      doc: string;
    };
    scheme: {
      type: string;
      values: {
        xyz: {
          doc: string;
        };
        tms: {
          doc: string;
        };
      };
      default: string;
      doc: string;
    };
    minzoom: {
      type: string;
      default: number;
      doc: string;
    };
    maxzoom: {
      type: string;
      default: number;
      doc: string;
    };
    attribution: {
      type: string;
      doc: string;
    };
    promoteId: {
      type: string;
      doc: string;
    };
    volatile: {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          android: string;
          ios: string;
          js: string;
        };
      };
    };
    encoding: {
      type: string;
      values: {
        mvt: {
          doc: string;
        };
        mlt: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        mvt: {
          android: string;
          ios: string;
          js: string;
        };
        mlt: {
          android: string;
          ios: string;
          js: string;
        };
      };
    };
    "*": {
      type: string;
      doc: string;
    };
  };
  source_raster: {
    type: {
      required: boolean;
      type: string;
      values: {
        raster: {
          doc: string;
        };
      };
      doc: string;
    };
    url: {
      type: string;
      doc: string;
    };
    tiles: {
      type: string;
      value: string;
      doc: string;
    };
    bounds: {
      type: string;
      value: string;
      length: number;
      default: number[];
      doc: string;
    };
    minzoom: {
      type: string;
      default: number;
      doc: string;
    };
    maxzoom: {
      type: string;
      default: number;
      doc: string;
    };
    tileSize: {
      type: string;
      default: number;
      units: string;
      doc: string;
    };
    scheme: {
      type: string;
      values: {
        xyz: {
          doc: string;
        };
        tms: {
          doc: string;
        };
      };
      default: string;
      doc: string;
    };
    attribution: {
      type: string;
      doc: string;
    };
    volatile: {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          android: string;
          ios: string;
          js: string;
        };
      };
    };
    "*": {
      type: string;
      doc: string;
    };
  };
  source_raster_dem: {
    type: {
      required: boolean;
      type: string;
      values: {
        "raster-dem": {
          doc: string;
        };
      };
      doc: string;
    };
    url: {
      type: string;
      doc: string;
    };
    tiles: {
      type: string;
      value: string;
      doc: string;
    };
    bounds: {
      type: string;
      value: string;
      length: number;
      default: number[];
      doc: string;
    };
    minzoom: {
      type: string;
      default: number;
      doc: string;
    };
    maxzoom: {
      type: string;
      default: number;
      doc: string;
    };
    tileSize: {
      type: string;
      default: number;
      units: string;
      doc: string;
    };
    attribution: {
      type: string;
      doc: string;
    };
    encoding: {
      type: string;
      values: {
        terrarium: {
          doc: string;
        };
        mapbox: {
          doc: string;
        };
        custom: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "mapbox, terrarium": {
          js: string;
          ios: string;
          android: string;
        };
        custom: {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    redFactor: {
      type: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    blueFactor: {
      type: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    greenFactor: {
      type: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    baseShift: {
      type: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    volatile: {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          android: string;
          ios: string;
          js: string;
        };
      };
    };
    "*": {
      type: string;
      doc: string;
    };
  };
  source_geojson: {
    type: {
      required: boolean;
      type: string;
      values: {
        geojson: {
          doc: string;
        };
      };
      doc: string;
    };
    data: {
      required: boolean;
      type: string;
      doc: string;
    };
    maxzoom: {
      type: string;
      default: number;
      doc: string;
    };
    attribution: {
      type: string;
      doc: string;
    };
    buffer: {
      type: string;
      default: number;
      maximum: number;
      minimum: number;
      doc: string;
    };
    filter: {
      type: string;
      doc: string;
    };
    tolerance: {
      type: string;
      default: number;
      doc: string;
    };
    cluster: {
      type: string;
      default: boolean;
      doc: string;
    };
    clusterRadius: {
      type: string;
      default: number;
      minimum: number;
      doc: string;
    };
    clusterMaxZoom: {
      type: string;
      doc: string;
    };
    clusterMinPoints: {
      type: string;
      doc: string;
    };
    clusterProperties: {
      type: string;
      doc: string;
    };
    lineMetrics: {
      type: string;
      default: boolean;
      doc: string;
    };
    generateId: {
      type: string;
      default: boolean;
      doc: string;
    };
    promoteId: {
      type: string;
      doc: string;
    };
  };
  source_video: {
    type: {
      required: boolean;
      type: string;
      values: {
        video: {
          doc: string;
        };
      };
      doc: string;
    };
    urls: {
      required: boolean;
      type: string;
      value: string;
      doc: string;
    };
    coordinates: {
      required: boolean;
      doc: string;
      type: string;
      length: number;
      value: {
        type: string;
        length: number;
        value: string;
        doc: string;
      };
    };
  };
  source_image: {
    type: {
      required: boolean;
      type: string;
      values: {
        image: {
          doc: string;
        };
      };
      doc: string;
    };
    url: {
      type: string;
      doc: string;
    };
    coordinates: {
      required: boolean;
      doc: string;
      type: string;
      length: number;
      value: {
        type: string;
        length: number;
        value: string;
        doc: string;
      };
    };
  };
  layer: {
    id: {
      type: string;
      doc: string;
      required: boolean;
    };
    type: {
      type: string;
      values: {
        fill: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        line: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        symbol: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        circle: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        heatmap: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        "fill-extrusion": {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        raster: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        hillshade: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
            "additional methods": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        "color-relief": {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        background: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
      };
      doc: string;
      required: boolean;
    };
    metadata: {
      type: string;
      doc: string;
      example: {
        "source:comment": string;
      };
    };
    source: {
      type: string;
      doc: string;
    };
    "source-layer": {
      type: string;
      doc: string;
    };
    minzoom: {
      type: string;
      minimum: number;
      maximum: number;
      doc: string;
    };
    maxzoom: {
      type: string;
      minimum: number;
      maximum: number;
      doc: string;
    };
    filter: {
      type: string;
      doc: string;
    };
    layout: {
      type: string;
      doc: string;
    };
    paint: {
      type: string;
      doc: string;
    };
  };
  layout: string[];
  layout_background: {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_fill: {
    "fill-sort-key": {
      type: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_circle: {
    "circle-sort-key": {
      type: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_heatmap: {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  "layout_fill-extrusion": {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-rounded-corner-distance": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
      "property-type": string;
    };
  };
  layout_line: {
    "line-cap": {
      type: string;
      values: {
        butt: {
          doc: string;
        };
        round: {
          doc: string;
        };
        square: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-join": {
      type: string;
      values: {
        bevel: {
          doc: string;
        };
        round: {
          doc: string;
        };
        miter: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-miter-limit": {
      type: string;
      default: number;
      doc: string;
      requires: {
        "line-join": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-round-limit": {
      type: string;
      default: number;
      doc: string;
      requires: {
        "line-join": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-sort-key": {
      type: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_symbol: {
    "symbol-placement": {
      type: string;
      values: {
        point: {
          doc: string;
        };
        line: {
          doc: string;
        };
        "line-center": {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "`line-center` value": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-spacing": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: {
        "symbol-placement": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-avoid-edges": {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-sort-key": {
      type: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-z-order": {
      type: string;
      values: {
        auto: {
          doc: string;
        };
        "viewport-y": {
          doc: string;
        };
        source: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-allow-overlap": {
      type: string;
      default: boolean;
      doc: string;
      requires: (string | {
        "!": string;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-overlap": {
      type: string;
      values: {
        never: {
          doc: string;
        };
        always: {
          doc: string;
        };
        cooperative: {
          doc: string;
        };
      };
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-ignore-placement": {
      type: string;
      default: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-optional": {
      type: string;
      default: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-rotation-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
        auto: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "`auto` value": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-size": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-text-fit": {
      type: string;
      values: {
        none: {
          doc: string;
        };
        width: {
          doc: string;
        };
        height: {
          doc: string;
        };
        both: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "stretchable icons": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-text-fit-padding": {
      type: string;
      value: string;
      length: number;
      default: number[];
      units: string;
      doc: string;
      requires: (string | {
        "icon-text-fit": string[];
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-image": {
      type: string;
      doc: string;
      tokens: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-rotate": {
      type: string;
      default: number;
      period: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-padding": {
      type: string;
      default: number[];
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-keep-upright": {
      type: string;
      default: boolean;
      doc: string;
      requires: (string | {
        "icon-rotation-alignment": string;
        "symbol-placement"?: undefined;
      } | {
        "symbol-placement": string[];
        "icon-rotation-alignment"?: undefined;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-offset": {
      type: string;
      value: string;
      length: number;
      default: number[];
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-anchor": {
      type: string;
      values: {
        center: {
          doc: string;
        };
        left: {
          doc: string;
        };
        right: {
          doc: string;
        };
        top: {
          doc: string;
        };
        bottom: {
          doc: string;
        };
        "top-left": {
          doc: string;
        };
        "top-right": {
          doc: string;
        };
        "bottom-left": {
          doc: string;
        };
        "bottom-right": {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-pitch-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
        auto: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-pitch-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
        auto: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "`auto` value": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-rotation-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
        "viewport-glyph": {
          doc: string;
        };
        auto: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "`auto` value": {
          js: string;
          android: string;
          ios: string;
        };
        "`viewport-glyph` value": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-field": {
      type: string;
      default: string;
      tokens: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-font": {
      type: string;
      value: string;
      default: string[];
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "local fonts": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-size": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-max-width": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-line-height": {
      type: string;
      default: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-letter-spacing": {
      type: string;
      default: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-justify": {
      type: string;
      values: {
        auto: {
          doc: string;
        };
        left: {
          doc: string;
        };
        center: {
          doc: string;
        };
        right: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        auto: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-radial-offset": {
      type: string;
      units: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      requires: string[];
      "property-type": string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
    };
    "text-variable-anchor": {
      type: string;
      value: string;
      values: {
        center: {
          doc: string;
        };
        left: {
          doc: string;
        };
        right: {
          doc: string;
        };
        top: {
          doc: string;
        };
        bottom: {
          doc: string;
        };
        "top-left": {
          doc: string;
        };
        "top-right": {
          doc: string;
        };
        "bottom-left": {
          doc: string;
        };
        "bottom-right": {
          doc: string;
        };
      };
      requires: (string | {
        "symbol-placement": string[];
      })[];
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      example: string[];
      "property-type": string;
    };
    "text-variable-anchor-offset": {
      type: string;
      requires: (string | {
        "symbol-placement": string[];
      })[];
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
        "data-driven styling": {
          js: string;
          ios: string;
          android: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      example: (string | number[])[];
      "property-type": string;
    };
    "text-anchor": {
      type: string;
      values: {
        center: {
          doc: string;
        };
        left: {
          doc: string;
        };
        right: {
          doc: string;
        };
        top: {
          doc: string;
        };
        bottom: {
          doc: string;
        };
        "top-left": {
          doc: string;
        };
        "top-right": {
          doc: string;
        };
        "bottom-left": {
          doc: string;
        };
        "bottom-right": {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: (string | {
        "!": string;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-max-angle": {
      type: string;
      default: number;
      units: string;
      doc: string;
      requires: (string | {
        "symbol-placement": string[];
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-writing-mode": {
      type: string;
      value: string;
      values: {
        horizontal: {
          doc: string;
        };
        vertical: {
          doc: string;
        };
      };
      doc: string;
      requires: (string | {
        "symbol-placement": string[];
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-rotate": {
      type: string;
      default: number;
      period: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-padding": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-keep-upright": {
      type: string;
      default: boolean;
      doc: string;
      requires: (string | {
        "text-rotation-alignment": string;
        "symbol-placement"?: undefined;
      } | {
        "symbol-placement": string[];
        "text-rotation-alignment"?: undefined;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-transform": {
      type: string;
      values: {
        none: {
          doc: string;
        };
        uppercase: {
          doc: string;
        };
        lowercase: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-offset": {
      type: string;
      doc: string;
      value: string;
      units: string;
      length: number;
      default: number[];
      requires: (string | {
        "!": string;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-allow-overlap": {
      type: string;
      default: boolean;
      doc: string;
      requires: (string | {
        "!": string;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-overlap": {
      type: string;
      values: {
        never: {
          doc: string;
        };
        always: {
          doc: string;
        };
        cooperative: {
          doc: string;
        };
      };
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-ignore-placement": {
      type: string;
      default: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-optional": {
      type: string;
      default: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-height-offset": {
      type: string;
      default: number;
      units: string;
      doc: string;
      requires: {
        "symbol-placement": string[];
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-height-anchor": {
      type: string;
      values: {
        ground: {
          doc: string;
        };
        absolute: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_raster: {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_hillshade: {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  "layout_color-relief": {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  filter: {
    type: string;
    doc: string;
    expression: {
      interpolated: boolean;
      parameters: string[];
    };
    "property-type": string;
  };
  filter_operator: {
    type: string;
    values: {
      "==": {
        doc: string;
      };
      "!=": {
        doc: string;
      };
      ">": {
        doc: string;
      };
      ">=": {
        doc: string;
      };
      "<": {
        doc: string;
      };
      "<=": {
        doc: string;
      };
      in: {
        doc: string;
      };
      "!in": {
        doc: string;
      };
      all: {
        doc: string;
      };
      any: {
        doc: string;
      };
      none: {
        doc: string;
      };
      has: {
        doc: string;
      };
      "!has": {
        doc: string;
      };
    };
    doc: string;
  };
  geometry_type: {
    type: string;
    values: {
      Point: {
        doc: string;
      };
      LineString: {
        doc: string;
      };
      Polygon: {
        doc: string;
      };
    };
    doc: string;
  };
  function: {
    expression: {
      type: string;
      doc: string;
    };
    stops: {
      type: string;
      doc: string;
      value: string;
    };
    base: {
      type: string;
      default: number;
      minimum: number;
      doc: string;
    };
    property: {
      type: string;
      doc: string;
      default: string;
    };
    type: {
      type: string;
      values: {
        identity: {
          doc: string;
        };
        exponential: {
          doc: string;
        };
        interval: {
          doc: string;
        };
        categorical: {
          doc: string;
        };
      };
      doc: string;
      default: string;
    };
    colorSpace: {
      type: string;
      values: {
        rgb: {
          doc: string;
        };
        lab: {
          doc: string;
        };
        hcl: {
          doc: string;
        };
      };
      doc: string;
      default: string;
    };
    default: {
      type: string;
      required: boolean;
      doc: string;
    };
  };
  function_stop: {
    type: string;
    minimum: number;
    maximum: number;
    value: string[];
    length: number;
    doc: string;
  };
  expression: {
    type: string;
    value: string;
    minimum: number;
    doc: string;
  };
  expression_name: {
    doc: string;
    type: string;
    values: {
      let: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number | (string | number | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      var: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      literal: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      semiliteral: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[][])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      array: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string[];
            doc: string;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | (string | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      at: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number | (string | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      in: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "index-of": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      slice: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      case: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | (string | boolean | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      match: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string[];
            doc: string;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      coalesce: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | (string | string[])[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      step: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      interpolate: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string[];
          }[];
          parameters: ({
            name: string;
            type: string;
            doc: string;
          } | {
            name: string;
            type: string[];
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "interpolate-hcl": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string[];
          }[];
          parameters: ({
            name: string;
            type: string;
            doc: string;
          } | {
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string[];
            doc?: undefined;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      "interpolate-lab": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string[];
          }[];
          parameters: ({
            name: string;
            type: string;
            doc: string;
          } | {
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string[];
            doc?: undefined;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      ln2: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      pi: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      e: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      typeof: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      string: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      number: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      boolean: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | boolean | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      object: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      collator: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: {
              "case-sensitive": {
                type: string;
                default: boolean;
                example: boolean;
                doc: string;
              };
              "diacritic-sensitive": {
                type: string;
                default: boolean;
                example: boolean;
                doc: string;
              };
              locale: {
                type: string;
                example: string;
                doc: string;
              };
            };
          }[];
        };
        example: (string | {
          "case-sensitive": boolean;
          "diacritic-sensitive": boolean;
          locale: string;
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      format: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string[];
          } | {
            name: string;
            type: {
              "text-font": {
                type: string;
                doc: string;
                example: string;
              };
              "text-color": {
                type: string;
                doc: string;
                example: string;
              };
              "font-scale": {
                type: string;
                doc: string;
                example: number;
              };
              "vertical-align": {
                type: string;
                doc: string;
                default: string;
                example: string;
                values: {
                  bottom: {
                    doc: string;
                  };
                  center: {
                    doc: string;
                  };
                  top: {
                    doc: string;
                  };
                };
              };
            };
          })[];
        };
        example: (string | (string | string[])[] | {
          "font-scale": number;
          "vertical-align"?: undefined;
        } | {
          "font-scale"?: undefined;
          "vertical-align"?: undefined;
        } | {
          "font-scale": number;
          "vertical-align": string;
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          "text-font": {
            js: string;
            android: string;
            ios: string;
          };
          "font-scale": {
            js: string;
            android: string;
            ios: string;
          };
          "text-color": {
            js: string;
            android: string;
            ios: string;
          };
          "vertical-align": {
            js: string;
            android: string;
            ios: string;
          };
          image: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      image: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "global-state": {
        doc: string;
        group: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "number-format": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc: string;
          } | {
            name: string;
            type: {
              locale: {
                type: string;
                example: string;
                doc: string;
              };
              currency: {
                type: string;
                example: string;
                doc: string;
              };
              unit: {
                type: string;
                example: string;
                doc: string;
              };
              "min-fraction-digits": {
                type: string;
                example: number;
                doc: string;
              };
              "max-fraction-digits": {
                type: string;
                example: number;
                doc: string;
              };
            };
            doc: string;
          })[];
        };
        example: (string | string[] | {
          "min-fraction-digits": number;
          "max-fraction-digits": number;
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          "`unit` property": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-string": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-number": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-boolean": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-rgba": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-color": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      rgb: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      rgba: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      get: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      has: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      length: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string[];
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      properties: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "feature-state": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      "geometry-type": {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      id: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      zoom: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "heatmap-density": {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      elevation: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "line-progress": {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      accumulated: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      "+": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "*": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "-": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "/": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "%": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "^": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      sqrt: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      log10: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      ln: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      log2: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      sin: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      cos: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      tan: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      asin: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      acos: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      atan: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      min: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      max: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      round: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      abs: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      ceil: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      floor: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      distance: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | {
          type: string;
          coordinates: number[];
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "==": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "!=": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | boolean)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      ">": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "<": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      ">=": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "<=": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      all: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | number | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      any: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | number | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "!": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      within: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | {
          type: string;
          coordinates: number[][][];
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "is-supported-script": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      upcase: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      downcase: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      concat: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "resolved-locale": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | {
          "case-sensitive": boolean;
          "diacritic-sensitive": boolean;
          locale: string;
        })[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      split: {
        doc: string;
        group: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      join: {
        doc: string;
        group: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | string[])[])[];
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
    };
  };
  light: {
    anchor: {
      type: string;
      default: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      "property-type": string;
      transition: boolean;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      doc: string;
      example: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    position: {
      type: string;
      default: number[];
      length: number;
      value: string;
      "property-type": string;
      transition: boolean;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      doc: string;
      example: number[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    color: {
      type: string;
      "property-type": string;
      default: string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    intensity: {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
  };
  sky: {
    "sky-color": {
      type: string;
      "property-type": string;
      default: string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "horizon-color": {
      type: string;
      "property-type": string;
      default: string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "fog-color": {
      type: string;
      "property-type": string;
      default: string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "fog-ground-blend": {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "horizon-fog-blend": {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "sky-horizon-blend": {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "atmosphere-blend": {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
  };
  terrain: {
    source: {
      type: string;
      doc: string;
      required: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    exaggeration: {
      type: string;
      minimum: number;
      doc: string;
      default: number;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
  };
  projection: {
    type: {
      type: string;
      doc: string;
      default: string;
      "property-type": string;
      transition: boolean;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
    };
  };
  paint: string[];
  paint_fill: {
    "fill-antialias": {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-layer-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "SDF fill pattern colorization": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-outline-color": {
      type: string;
      doc: string;
      transition: boolean;
      requires: ({
        "!": string;
        "fill-antialias"?: undefined;
      } | {
        "fill-antialias": boolean;
        "!"?: undefined;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-pattern": {
      type: string;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  "paint_fill-extrusion": {
    "fill-extrusion-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      requires: {
        "!": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-pattern": {
      type: string;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-height": {
      type: string;
      default: number;
      units: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
        "negative values": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-base": {
      type: string;
      default: number;
      units: string;
      doc: string;
      transition: boolean;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
        "negative values": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-vertical-gradient": {
      type: string;
      default: boolean;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_line: {
    "line-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-layer-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-color": {
      type: string;
      doc: string;
      default: string;
      transition: boolean;
      requires: {
        "!": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-width": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-gap-width": {
      type: string;
      default: number;
      minimum: number;
      doc: string;
      transition: boolean;
      units: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-offset": {
      type: string;
      default: number;
      doc: string;
      transition: boolean;
      units: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-blur": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-dasharray": {
      type: string;
      value: string;
      doc: string;
      minimum: number;
      transition: boolean;
      units: string;
      requires: {
        "!": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          ios: string;
          android: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-pattern": {
      type: string;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-gradient": {
      type: string;
      doc: string;
      transition: boolean;
      requires: ({
        "!": string;
        source?: undefined;
        has?: undefined;
      } | {
        source: string;
        has: {
          lineMetrics: boolean;
        };
        "!"?: undefined;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {};
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_circle: {
    "circle-radius": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-blur": {
      type: string;
      default: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-pitch-scale": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-pitch-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-stroke-width": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-stroke-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-stroke-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_heatmap: {
    "heatmap-radius": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "heatmap-weight": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "heatmap-intensity": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "heatmap-color": {
      type: string;
      default: (string | number | string[])[];
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {};
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "heatmap-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_symbol: {
    "icon-opacity": {
      doc: string;
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-color": {
      type: string;
      default: string;
      transition: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-halo-color": {
      type: string;
      default: string;
      transition: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-halo-width": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-halo-blur": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-color": {
      type: string;
      doc: string;
      default: string;
      transition: boolean;
      overridable: boolean;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-halo-color": {
      type: string;
      default: string;
      transition: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-halo-width": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-halo-blur": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_raster: {
    "raster-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-hue-rotate": {
      type: string;
      default: number;
      period: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-brightness-min": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-brightness-max": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-saturation": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-contrast": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    resampling: {
      type: string;
      doc: string;
      values: {
        linear: {
          doc: string;
        };
        nearest: {
          doc: string;
        };
      };
      default: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-resampling": {
      type: string;
      doc: string;
      values: {
        linear: {
          doc: string;
        };
        nearest: {
          doc: string;
        };
      };
      default: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-fade-duration": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_hillshade: {
    "hillshade-illumination-direction": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        multidirectional: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-illumination-altitude": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        multidirectional: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-illumination-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-exaggeration": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-shadow-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        multidirectional: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-highlight-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        multidirectional: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-accent-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-method": {
      type: string;
      values: {
        standard: {
          doc: string;
        };
        basic: {
          doc: string;
        };
        combined: {
          doc: string;
        };
        igor: {
          doc: string;
        };
        multidirectional: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    resampling: {
      type: string;
      doc: string;
      values: {
        linear: {
          doc: string;
        };
        nearest: {
          doc: string;
        };
      };
      default: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  "paint_color-relief": {
    "color-relief-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "color-relief-color": {
      type: string;
      doc: string;
      example: (string | number | string[])[];
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {};
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    resampling: {
      type: string;
      doc: string;
      values: {
        linear: {
          doc: string;
        };
        nearest: {
          doc: string;
        };
      };
      default: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_background: {
    "background-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      requires: {
        "!": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "background-pattern": {
      type: string;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {};
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "background-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  transition: {
    duration: {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
    };
    delay: {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
    };
  };
  "property-type": {
    "data-driven": {
      type: string;
      doc: string;
    };
    "cross-faded": {
      type: string;
      doc: string;
    };
    "cross-faded-data-driven": {
      type: string;
      doc: string;
    };
    "color-ramp": {
      type: string;
      doc: string;
    };
    "data-constant": {
      type: string;
      doc: string;
    };
    constant: {
      type: string;
      doc: string;
    };
  };
  promoteId: {
    "*": {
      type: string;
      doc: string;
    };
  };
  interpolation: {
    type: string;
    value: string;
    minimum: number;
    doc: string;
  };
  interpolation_name: {
    doc: string;
    type: string;
    values: {
      linear: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
          parameters: any[];
        };
        example: string[];
        "sdk-support": {
          interpolate: {
            js: string;
            android: string;
            ios: string;
          };
          "interpolate-hcl": {
            js: string;
            ios: string;
            android: string;
          };
          "interpolate-lab": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      exponential: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        "sdk-support": {
          interpolate: {
            js: string;
            android: string;
            ios: string;
          };
          "interpolate-hcl": {
            js: string;
            ios: string;
            android: string;
          };
          "interpolate-lab": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      "cubic-bezier": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        "sdk-support": {
          interpolate: {
            js: string;
            android: string;
            ios: string;
          };
          "interpolate-hcl": {
            js: string;
            ios: string;
            android: string;
          };
          "interpolate-lab": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
    };
  };
};
//#endregion
//#region src/reference/latest.d.ts
/**
 * The style specification reference, i.e. the contents of `v8.json`, Inferred from the JSON itself.
 */
type StyleSpecificationReference = typeof _exports;
declare const latest: StyleSpecificationReference;
//#endregion
//#region src/types.g.d.ts
type ColorSpecification = string;
type ProjectionDefinitionT = [string, string, number];
type ProjectionDefinitionSpecification = string | ProjectionDefinitionT | PropertyValueSpecification<ProjectionDefinitionT>;
type PaddingSpecification = number | number[];
type NumberArraySpecification = number | number[];
type ColorArraySpecification = string | string[];
type VariableAnchorOffsetCollectionSpecification = Array<string | [number, number]>;
type SpriteSpecification = string | {
  id: string;
  url: string;
}[];
type FormattedSpecification = string;
type ResolvedImageSpecification = string;
type PromoteIdSpecification = {
  [_: string]: string;
} | string;
type ExpressionInputType = string | number | boolean;
type VariableExpressionSpecification = ['var', string];
type CollatorExpressionSpecification = ['collator', {
  'case-sensitive'?: boolean | ExpressionSpecification;
  'diacritic-sensitive'?: boolean | ExpressionSpecification;
  locale?: string | ExpressionSpecification;
}];
type InterpolationSpecification = ['linear'] | ['exponential', number] | ['cubic-bezier', number, number, number, number];
type ExpressionSpecification = ['array', ExpressionSpecification] | ['array', 'string' | 'number' | 'boolean', ExpressionSpecification] | ['array', 'string' | 'number' | 'boolean', number, ExpressionSpecification] | ['boolean', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] | CollatorExpressionSpecification | ['format', ...(string | ['image', ExpressionSpecification] | ExpressionSpecification | {
  'font-scale'?: number | ExpressionSpecification;
  'text-font'?: ExpressionSpecification;
  'text-color'?: ColorSpecification | ExpressionSpecification;
  'vertical-align'?: 'bottom' | 'center' | 'top';
})[]] | ['image', string | ExpressionSpecification] | ['literal', unknown] | ['semiliteral', unknown] | ['number', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] | ['number-format', number | ExpressionSpecification, {
  'locale'?: string | ExpressionSpecification;
  'currency'?: string | ExpressionSpecification;
  'min-fraction-digits'?: number | ExpressionSpecification;
  'max-fraction-digits'?: number | ExpressionSpecification;
}] | ['number-format', number | ExpressionSpecification, {
  'locale'?: string | ExpressionSpecification;
  'unit'?: string | ExpressionSpecification;
  'min-fraction-digits'?: number | ExpressionSpecification;
  'max-fraction-digits'?: number | ExpressionSpecification;
}] | ['object', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] | ['string', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] | ['to-boolean', unknown | ExpressionSpecification] | ['to-color', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] | ['to-number', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] | ['to-string', unknown | ExpressionSpecification] | ['typeof', unknown | ExpressionSpecification] | ['accumulated'] | ['feature-state', string | ExpressionSpecification] | ['geometry-type'] | ['id'] | ['line-progress'] | ['properties'] | ['at', number | ExpressionSpecification, ExpressionSpecification] | ['get', string | ExpressionSpecification, ExpressionSpecification?] | ['global-state', string] | ['has', string | ExpressionSpecification, ExpressionSpecification?] | ['in', null | ExpressionInputType | ExpressionSpecification, string | ExpressionSpecification] | ['index-of', null | ExpressionInputType | ExpressionSpecification, string | ExpressionSpecification, (number | ExpressionSpecification)?] | ['length', string | ExpressionSpecification] | ['slice', string | ExpressionSpecification, number | ExpressionSpecification, (number | ExpressionSpecification)?] | ['!', boolean | ExpressionSpecification] | ['!=', null | ExpressionInputType | ExpressionSpecification, null | ExpressionInputType | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] | ['<', string | number | ExpressionSpecification, string | number | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] | ['<=', string | number | ExpressionSpecification, string | number | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] | ['==', null | ExpressionInputType | ExpressionSpecification, null | ExpressionInputType | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] | ['>', string | number | ExpressionSpecification, string | number | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] | ['>=', string | number | ExpressionSpecification, string | number | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] | ['all', ...(boolean | ExpressionSpecification)[]] | ['any', ...(boolean | ExpressionSpecification)[]] | ['case', boolean | ExpressionSpecification, null | ExpressionInputType | ExpressionSpecification, ...(boolean | null | ExpressionInputType | ExpressionSpecification)[], null | ExpressionInputType | ExpressionSpecification] | ['coalesce', ...(ExpressionInputType | ExpressionSpecification)[]] | ['match', string | number | ExpressionSpecification, string | number | string[] | number[], null | ExpressionInputType | ExpressionSpecification, ...(string | number | string[] | number[] | null | ExpressionInputType | ExpressionSpecification)[],
// repeated as above
null | ExpressionInputType | ExpressionSpecification] | ['within', GeoJSON.GeoJSON] | ['interpolate', InterpolationSpecification, number | ExpressionSpecification, ...(number | ColorSpecification | ExpressionSpecification | ProjectionDefinitionSpecification)[]] | ['interpolate-hcl', InterpolationSpecification, number | ExpressionSpecification, ...(number | ColorSpecification | ExpressionSpecification)[]] | ['interpolate-lab', InterpolationSpecification, number | ExpressionSpecification, ...(number | ColorSpecification | ExpressionSpecification)[]] | ['step', number | ExpressionSpecification, ExpressionInputType | ExpressionSpecification, ...(number | ExpressionInputType | ExpressionSpecification)[]] | ['let', string, ExpressionInputType | ExpressionSpecification, ...(string | ExpressionInputType | ExpressionSpecification)[]] | VariableExpressionSpecification | ['concat', ...(ExpressionInputType | ExpressionSpecification)[]] | ['downcase', string | ExpressionSpecification] | ['is-supported-script', string | ExpressionSpecification] | ['join', string[] | ExpressionSpecification, string | ExpressionSpecification] | ['resolved-locale', CollatorExpressionSpecification] | ['split', string | ExpressionSpecification, string | ExpressionSpecification] | ['upcase', string | ExpressionSpecification] | ['rgb', number | ExpressionSpecification, number | ExpressionSpecification, number | ExpressionSpecification] | ['rgba', number | ExpressionSpecification, number | ExpressionSpecification, number | ExpressionSpecification, number | ExpressionSpecification] | ['to-rgba', ColorSpecification | ExpressionSpecification] | ['-', number | ExpressionSpecification, (number | ExpressionSpecification)?] | ['*', number | ExpressionSpecification, number | ExpressionSpecification, ...(number | ExpressionSpecification)[]] | ['/', number | ExpressionSpecification, number | ExpressionSpecification] | ['%', number | ExpressionSpecification, number | ExpressionSpecification] | ['^', number | ExpressionSpecification, number | ExpressionSpecification] | ['+', ...(number | ExpressionSpecification)[]] | ['abs', number | ExpressionSpecification] | ['acos', number | ExpressionSpecification] | ['asin', number | ExpressionSpecification] | ['atan', number | ExpressionSpecification] | ['ceil', number | ExpressionSpecification] | ['cos', number | ExpressionSpecification] | ['distance', GeoJSON.GeoJSON] | ['e'] | ['floor', number | ExpressionSpecification] | ['ln', number | ExpressionSpecification] | ['ln2'] | ['log10', number | ExpressionSpecification] | ['log2', number | ExpressionSpecification] | ['max', number | ExpressionSpecification, ...(number | ExpressionSpecification)[]] | ['min', number | ExpressionSpecification, ...(number | ExpressionSpecification)[]] | ['pi'] | ['round', number | ExpressionSpecification] | ['sin', number | ExpressionSpecification] | ['sqrt', number | ExpressionSpecification] | ['tan', number | ExpressionSpecification] | ['zoom'] | ['heatmap-density'] | ['elevation'] | ['global-state', string];
type ExpressionFilterSpecification = boolean | ExpressionSpecification;
type LegacyFilterSpecification = ['has', string] | ['!has', string] | ['==', string, string | number | boolean] | ['!=', string, string | number | boolean] | ['>', string, string | number | boolean] | ['>=', string, string | number | boolean] | ['<', string, string | number | boolean] | ['<=', string, string | number | boolean] | ['in', string, ...(string | number | boolean)[]] | ['!in', string, ...(string | number | boolean)[]] | ['all', ...LegacyFilterSpecification[]] | ['any', ...LegacyFilterSpecification[]] | ['none', ...LegacyFilterSpecification[]];
type FilterSpecification = ExpressionFilterSpecification | LegacyFilterSpecification;
type VisibilitySpecification = 'visible' | 'none' | ExpressionSpecification;
type TransitionSpecification = {
  duration?: number;
  delay?: number;
};
type CameraFunctionSpecification<T> = {
  type: 'exponential';
  stops: Array<[number, T]>;
} | {
  type: 'interval';
  stops: Array<[number, T]>;
};
type SourceFunctionSpecification<T> = {
  type: 'exponential';
  stops: Array<[number, T]>;
  property: string;
  default?: T;
} | {
  type: 'interval';
  stops: Array<[number, T]>;
  property: string;
  default?: T;
} | {
  type: 'categorical';
  stops: Array<[string | number | boolean, T]>;
  property: string;
  default?: T;
} | {
  type: 'identity';
  property: string;
  default?: T;
};
type CompositeFunctionSpecification<T> = {
  type: 'exponential';
  stops: Array<[{
    zoom: number;
    value: number;
  }, T]>;
  property: string;
  default?: T;
} | {
  type: 'interval';
  stops: Array<[{
    zoom: number;
    value: number;
  }, T]>;
  property: string;
  default?: T;
} | {
  type: 'categorical';
  stops: Array<[{
    zoom: number;
    value: string | number | boolean;
  }, T]>;
  property: string;
  default?: T;
};
type PropertyValueSpecification<T> = T | CameraFunctionSpecification<T> | ExpressionSpecification;
type DataDrivenPropertyValueSpecification<T> = T | CameraFunctionSpecification<T> | SourceFunctionSpecification<T> | CompositeFunctionSpecification<T> | ExpressionSpecification;
type SchemaSpecification = {
  default?: unknown;
};
type StateSpecification = Record<string, SchemaSpecification>;
type MLFontFace = {
  url: string;
  "unicode-range"?: string[];
};
type FontFacesSpecification = Record<string, string | Array<MLFontFace>>;
type StyleSpecification = {
  /**
   * Style specification version number. Must be 8.
   *
   * @example
   * ```json
   * 8
   * ```
   */
  "version": 8;
  /**
   * A human-readable name for the style.
   *
   * @example
   * ```json
   * "Bright"
   * ```
   */
  "name"?: string;
  /**
   * Arbitrary properties useful to track with the stylesheet, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {
   *     "styleeditor:slimmode": true,
   *     "styleeditor:comment": "Style generated 1677776383",
   *     "styleeditor:version": "3.14.159265",
   *     "example:object": {
   *         "String": "one",
   *         "Number": 2,
   *         "Boolean": false
   *     }
   * }
   * ```
   */
  "metadata"?: unknown;
  /**
   * Default map center in longitude and latitude.  The style center will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
   *
   * @example
   * ```json
   * [-73.9749, 40.7736]
   * ```
   */
  "center"?: [number, number];
  /**
   * Default map center altitude in meters above sea level. The style center altitude defines the altitude where the camera is looking at and will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
   *
   * @example
   * ```json
   * 123.4
   * ```
   */
  "centerAltitude"?: number;
  /**
   * Default zoom level.  The style zoom will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
   *
   * @example
   * ```json
   * 12.5
   * ```
   */
  "zoom"?: number;
  /**
   * Default bearing, in degrees. The bearing is the compass direction that is "up"; for example, a bearing of 90° orients the map so that east is up. This value will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
   *
   * @example
   * ```json
   * 29
   * ```
   */
  "bearing"?: number;
  /**
   * Default pitch, in degrees. Zero is perpendicular to the surface, for a look straight down at the map, while a greater value like 60 looks ahead towards the horizon. The style pitch will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
   *
   * @example
   * ```json
   * 50
   * ```
   */
  "pitch"?: number;
  /**
   * Default roll, in degrees. The roll angle is measured counterclockwise about the camera boresight. The style roll will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
   *
   * @example
   * ```json
   * 45
   * ```
   */
  "roll"?: number;
  /**
   * An object used to define default values when using the [`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression.
   *
   * @default
   * ```json
   * {}
   * ```
   *
   * @example
   * ```json
   * {
   *     "chargerType": {"default": ["CCS", "CHAdeMO", "Type2"]},
   *     "minPreferredChargingSpeed": {"default": 50}
   * }
   * ```
   */
  "state"?: StateSpecification;
  /**
   * The global light source.
   *
   * @example
   * ```json
   * {"anchor": "viewport", "color": "white", "intensity": 0.4}
   * ```
   */
  "light"?: LightSpecification;
  /**
   * The map's sky configuration. **Note:** this definition is still experimental and is under development in maplibre-gl-js.
   *
   * @example
   * ```json
   * {
   *     "sky-color": "#199EF3",
   *     "sky-horizon-blend": 0.5,
   *     "horizon-color": "#ffffff",
   *     "horizon-fog-blend": 0.5,
   *     "fog-color": "#0000ff",
   *     "fog-ground-blend": 0.5,
   *     "atmosphere-blend": [
   *         "interpolate",
   *         ["linear"],
   *         ["zoom"],
   *         0,
   *         1,
   *         10,
   *         1,
   *         12,
   *         0
   *     ]
   * }
   * ```
   */
  "sky"?: SkySpecification;
  /**
   * The projection configuration
   *
   * @example
   * ```json
   * {
   *     "type": [
   *         "interpolate",
   *         ["linear"],
   *         ["zoom"],
   *         10,
   *         "vertical-perspective",
   *         12,
   *         "mercator"
   *     ]
   * }
   * ```
   */
  "projection"?: ProjectionSpecification;
  /**
   * The terrain configuration.
   *
   * @example
   * ```json
   * {"source": "raster-dem-source", "exaggeration": 0.5}
   * ```
   */
  "terrain"?: TerrainSpecification;
  /**
   * Sources state which data the map should display. Specify the type of source with the `type` property. Adding a source isn't enough to make data appear on the map because sources don't contain styling details like color or width. Layers refer to a source and give it a visual representation. This makes it possible to style the same source in different ways, like differentiating between types of roads in a highways layer.
   *
   * Tiled sources (vector and raster) must specify their details according to the [TileJSON specification](https://github.com/mapbox/tilejson-spec).
   *
   * @example
   * ```json
   * {
   *     "maplibre-demotiles": {
   *         "type": "vector",
   *         "url": "https://demotiles.maplibre.org/tiles/tiles.json"
   *     },
   *     "maplibre-tilejson": {
   *         "type": "vector",
   *         "url": "http://api.example.com/tilejson.json"
   *     },
   *     "maplibre-streets": {
   *         "type": "vector",
   *         "tiles": [
   *             "http://a.example.com/tiles/{z}/{x}/{y}.pbf",
   *             "http://b.example.com/tiles/{z}/{x}/{y}.pbf"
   *         ],
   *         "maxzoom": 14
   *     },
   *     "wms-imagery": {
   *         "type": "raster",
   *         "tiles": [
   *             "http://a.example.com/wms?bbox={bbox-epsg-3857}&format=image/png&service=WMS&version=1.1.1&request=GetMap&srs=EPSG:3857&width=256&height=256&layers=example"
   *         ],
   *         "tileSize": 256
   *     }
   * }
   * ```
   */
  "sources": {
    [_: string]: SourceSpecification;
  };
  /**
   * An array of `{id: 'my-sprite', url: 'https://example.com/sprite'}` objects. Each object should represent a unique URL to load a sprite from and and a unique ID to use as a prefix when referencing images from that sprite (i.e. 'my-sprite:image'). All the URLs are internally extended to load both .json and .png files. If the `id` field is equal to 'default', the prefix is omitted (just 'image' instead of 'default:image'). All the IDs and URLs must be unique. For backwards compatibility, instead of an array, one can also provide a single string that represent a URL to load the sprite from. The images in this case won't be prefixed.
   *
   * @example
   * ```json
   * "https://demotiles.maplibre.org/styles/osm-bright-gl-style/sprite"
   * ```
   */
  "sprite"?: SpriteSpecification;
  /**
   * A URL template for loading signed-distance-field glyph sets in PBF format.
   *
   * If this property is set, any text in the `text-field` layout property is displayed in the font stack named by the `text-font` layout property based on glyphs located at the URL specified by this property. Otherwise, font faces will be determined by the `text-font` property based on the local environment.
   *
   * The URL must include:
   *
   *  - `{fontstack}` - When requesting glyphs, this token is replaced with a comma separated list of fonts from a font stack specified in the `text-font` property of a symbol layer.
   *
   *  - `{range}` - When requesting glyphs, this token is replaced with a range of 256 Unicode code points. For example, to load glyphs for the Unicode Basic Latin and Basic Latin-1 Supplement blocks, the range would be 0-255. The actual ranges that are loaded are determined at runtime based on what text needs to be displayed.
   *
   * The URL must be absolute, containing the [scheme, authority and path components](https://en.wikipedia.org/wiki/URL#Syntax).
   *
   * @example
   * ```json
   * "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf"
   * ```
   */
  "glyphs"?: string;
  /**
   * The `font-faces` property can be used to specify what font files to use for rendering text. Font faces contain information needed to render complex texts such as [Devanagari](https://en.wikipedia.org/wiki/Devanagari), [Khmer](https://en.wikipedia.org/wiki/Khmer_script) among many others.<h2>Unicode range</h2>The optional `unicode-range` property can be used to only use a particular font file for characters within the specified unicode range(s). Its value should be an array of strings, each indicating a start and end of a unicode range, similar to the [CSS descriptor with the same name](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/unicode-range). This allows specifying multiple non-consecutive unicode ranges. When not specified, the default value is `U+0-10FFFF`, meaning the font file will be used for all unicode characters.
   *
   * Refer to the [Unicode Character Code Charts](https://www.unicode.org/charts/) to see ranges for scripts supported by Unicode. To see what unicode code-points are available in a font, use a tool like [FontDrop](https://fontdrop.info/).
   *
   * <h2>Font Resolution</h2>For every name in a symbol layer’s [`text-font`](./layers.md#text-font) array, characters are matched if they are covered one of the by the font files in the corresponding entry of the `font-faces` map. Any still-unmatched characters then fall back to the [`glyphs`](./glyphs.md) URL if provided.
   *
   * <h2>Supported Fonts</h2>What type of fonts are supported is implementation-defined. Unsupported fonts are ignored.
   *
   * @example
   * ```json
   * {
   *     "Noto Sans Regular": [
   *         {
   *             "url": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansKhmer/hinted/ttf/NotoSansKhmer-Regular.ttf",
   *             "unicode-range": ["U+1780-17FF"]
   *         },
   *         {
   *             "url": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansDevanagari/hinted/ttf/NotoSansDevanagari-Regular.ttf",
   *             "unicode-range": ["U+0900-097F"]
   *         },
   *         {
   *             "url": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansMyanmar/hinted/ttf/NotoSansMyanmar-Regular.ttf",
   *             "unicode-range": ["U+1000-109F"]
   *         },
   *         {
   *             "url": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansEthiopic/hinted/ttf/NotoSansEthiopic-Regular.ttf",
   *             "unicode-range": ["U+1200-137F"]
   *         }
   *     ],
   *     "Unifont": "https://ftp.gnu.org/gnu/unifont/unifont-15.0.01/unifont-15.0.01.ttf"
   * }
   * ```
   */
  "font-faces"?: FontFacesSpecification;
  /**
   * A global transition definition to use as a default across properties, to be used for timing transitions between one value and the next when no property-specific transition is set. Collision-based symbol fading is controlled independently of the style's `transition` property.
   *
   * In addition to this global definition via `transition`, if any individual paint or layout property are marked as `Transitionable`, a corresponding `*-transition` property is avaliable to fine-tune the property’s animation between old and new values based on similar `duration` and `delay` values.
   *
   * For example, [`fill-color`](layers/#fill-color) is marked as `Transitionable`, so it can transition either independently via `fill-color-transition` or globally via the style's `transition` property:
   *
   * @example
   * ```json
   * {"duration": 300, "delay": 0}
   * ```
   */
  "transition"?: TransitionSpecification;
  /**
   * A style's `layers` property lists all the layers available in that style. The type of layer is specified by the `type` property, and must be one of `background`, `fill`, `line`, `symbol`, `raster`, `circle`, `fill-extrusion`, `heatmap`, `hillshade`, `color-relief`.
   *
   * Except for layers of the `background` type, each layer needs to refer to a source. Layers take the data that they get from a source, optionally filter features, and then define how those features are styled.
   *
   * @example
   * ```json
   * [
   *     {
   *         "id": "coastline",
   *         "source": "maplibre",
   *         "source-layer": "countries",
   *         "type": "line",
   *         "paint": {"line-color": "#198EC8"}
   *     }
   * ]
   * ```
   */
  "layers": Array<LayerSpecification>;
};
type LightSpecification = {
  /**
   * Whether extruded geometries are lit relative to the map or viewport.
   *
   * @default
   * ```json
   * "viewport"
   * ```
   *
   * @example
   * ```json
   * "map"
   * ```
   */
  "anchor"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * Position of the light source relative to lit (extruded) geometries, in `[r radial coordinate, a azimuthal angle, p polar angle]` where r indicates the distance from the center of the base of an object to its light, a indicates the position of the light relative to 0° (0° when `light.anchor` is set to `viewport` corresponds to the top of the viewport, or 0° when `light.anchor` is set to `map` corresponds to due north, and degrees proceed clockwise), and p indicates the height of the light (from 0°, directly above, to 180°, directly below).
   *
   * @default
   * ```json
   * [1.15, 210, 30]
   * ```
   *
   * @example
   * ```json
   * [1.5, 90, 80]
   * ```
   */
  "position"?: PropertyValueSpecification<[number, number, number]>;
  "position-transition"?: TransitionSpecification;
  /**
   * Color tint for lighting extruded geometries.
   *
   * @default
   * ```json
   * "#ffffff"
   * ```
   */
  "color"?: PropertyValueSpecification<ColorSpecification>;
  "color-transition"?: TransitionSpecification;
  /**
   * Intensity of lighting (on a scale from 0 to 1). Higher numbers will present as more extreme contrast.
   *
   * @default
   * ```json
   * 0.5
   * ```
   */
  "intensity"?: PropertyValueSpecification<number>;
  "intensity-transition"?: TransitionSpecification;
};
type SkySpecification = {
  /**
   * The base color for the sky.
   *
   * @default
   * ```json
   * "#88C6FC"
   * ```
   */
  "sky-color"?: PropertyValueSpecification<ColorSpecification>;
  "sky-color-transition"?: TransitionSpecification;
  /**
   * The base color at the horizon.
   *
   * @default
   * ```json
   * "#ffffff"
   * ```
   */
  "horizon-color"?: PropertyValueSpecification<ColorSpecification>;
  "horizon-color-transition"?: TransitionSpecification;
  /**
   * The base color for the fog. Requires 3D terrain.
   *
   * @default
   * ```json
   * "#ffffff"
   * ```
   */
  "fog-color"?: PropertyValueSpecification<ColorSpecification>;
  "fog-color-transition"?: TransitionSpecification;
  /**
   * How to blend the fog over the 3D terrain. Where 0 is the map center and 1 is the horizon.
   *
   * @default
   * ```json
   * 0.5
   * ```
   */
  "fog-ground-blend"?: PropertyValueSpecification<number>;
  "fog-ground-blend-transition"?: TransitionSpecification;
  /**
   * How to blend the fog color and the horizon color. Where 0 is using the horizon color only and 1 is using the fog color only.
   *
   * @default
   * ```json
   * 0.8
   * ```
   */
  "horizon-fog-blend"?: PropertyValueSpecification<number>;
  "horizon-fog-blend-transition"?: TransitionSpecification;
  /**
   * How to blend the sky color and the horizon color. Where 1 is blending the color at the middle of the sky and 0 is not blending at all and using the sky color only.
   *
   * @default
   * ```json
   * 0.8
   * ```
   */
  "sky-horizon-blend"?: PropertyValueSpecification<number>;
  "sky-horizon-blend-transition"?: TransitionSpecification;
  /**
   * How to blend the atmosphere. Where 1 is visible atmosphere and 0 is hidden. It is best to interpolate this expression when using globe projection.
   *
   * @default
   * ```json
   * 0.8
   * ```
   */
  "atmosphere-blend"?: PropertyValueSpecification<number>;
  "atmosphere-blend-transition"?: TransitionSpecification;
};
type ProjectionSpecification = {
  /**
   * The projection definition type. Can be specified as a string, a transition state, or an expression.
   *
   * @default
   * ```json
   * "mercator"
   * ```
   */
  "type"?: PropertyValueSpecification<ProjectionDefinitionSpecification>;
};
type TerrainSpecification = {
  /**
   * The source for the terrain data.
   */
  "source": string;
  /**
   * The exaggeration of the terrain - how high it will look.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "exaggeration"?: number;
};
type VectorSourceSpecification = {
  /**
   * The type of the source.
   */
  "type": "vector";
  /**
   * A URL to a TileJSON resource. Supported protocols are `http:` and `https:`.
   */
  "url"?: string;
  /**
   * An array of one or more tile source URLs, as in the TileJSON spec.
   */
  "tiles"?: Array<string>;
  /**
   * An array containing the longitude and latitude of the southwest and northeast corners of the source's bounding box in the following order: `[sw.lng, sw.lat, ne.lng, ne.lat]`. When this property is included in a source, no tiles outside of the given bounds are requested by MapLibre.
   *
   * @default
   * ```json
   * [-180, -85.051129, 180, 85.051129]
   * ```
   */
  "bounds"?: [number, number, number, number];
  /**
   * Influences the y direction of the tile coordinates. The global-mercator (aka Spherical Mercator) profile is assumed.
   *
   * @default
   * ```json
   * "xyz"
   * ```
   */
  "scheme"?: "xyz" | "tms";
  /**
   * Minimum zoom level for which tiles are available, as in the TileJSON spec.
   */
  "minzoom"?: number;
  /**
   * Maximum zoom level for which tiles are available, as in the TileJSON spec. Data from tiles at the maxzoom are used when displaying the map at higher zoom levels.
   *
   * @default
   * ```json
   * 22
   * ```
   */
  "maxzoom"?: number;
  /**
   * Contains an attribution to be displayed when the map is shown to a user.
   */
  "attribution"?: string;
  /**
   * A property to use as a feature id (for feature state). Either a property name, or an object of the form `{<sourceLayer>: <propertyName>}`. If specified as a string for a vector tile source, the same property is used across all its source layers.
   */
  "promoteId"?: PromoteIdSpecification;
  /**
   * A setting to determine whether a source's tiles are cached locally.
   */
  "volatile"?: boolean;
  /**
   * The encoding used by this source. Mapbox Vector Tiles encoding is used by default.
   *
   * @default
   * ```json
   * "mvt"
   * ```
   */
  "encoding"?: "mvt" | "mlt";
};
type RasterSourceSpecification = {
  /**
   * The type of the source.
   */
  "type": "raster";
  /**
   * A URL to a TileJSON resource. Supported protocols are `http:` and `https:`.
   */
  "url"?: string;
  /**
   * An array of one or more tile source URLs, as in the TileJSON spec.
   */
  "tiles"?: Array<string>;
  /**
   * An array containing the longitude and latitude of the southwest and northeast corners of the source's bounding box in the following order: `[sw.lng, sw.lat, ne.lng, ne.lat]`. When this property is included in a source, no tiles outside of the given bounds are requested by MapLibre.
   *
   * @default
   * ```json
   * [-180, -85.051129, 180, 85.051129]
   * ```
   */
  "bounds"?: [number, number, number, number];
  /**
   * Minimum zoom level for which tiles are available, as in the TileJSON spec.
   */
  "minzoom"?: number;
  /**
   * Maximum zoom level for which tiles are available, as in the TileJSON spec. Data from tiles at the maxzoom are used when displaying the map at higher zoom levels.
   *
   * @default
   * ```json
   * 22
   * ```
   */
  "maxzoom"?: number;
  /**
   * The minimum visual size to display tiles for this layer. Only configurable for raster layers.
   *
   * @default
   * ```json
   * 512
   * ```
   */
  "tileSize"?: number;
  /**
   * Influences the y direction of the tile coordinates. The global-mercator (aka Spherical Mercator) profile is assumed.
   *
   * @default
   * ```json
   * "xyz"
   * ```
   */
  "scheme"?: "xyz" | "tms";
  /**
   * Contains an attribution to be displayed when the map is shown to a user.
   */
  "attribution"?: string;
  /**
   * A setting to determine whether a source's tiles are cached locally.
   */
  "volatile"?: boolean;
};
type RasterDEMSourceSpecification = {
  /**
   * The type of the source.
   */
  "type": "raster-dem";
  /**
   * A URL to a TileJSON resource. Supported protocols are `http:` and `https:`.
   */
  "url"?: string;
  /**
   * An array of one or more tile source URLs, as in the TileJSON spec.
   */
  "tiles"?: Array<string>;
  /**
   * An array containing the longitude and latitude of the southwest and northeast corners of the source's bounding box in the following order: `[sw.lng, sw.lat, ne.lng, ne.lat]`. When this property is included in a source, no tiles outside of the given bounds are requested by MapLibre.
   *
   * @default
   * ```json
   * [-180, -85.051129, 180, 85.051129]
   * ```
   */
  "bounds"?: [number, number, number, number];
  /**
   * Minimum zoom level for which tiles are available, as in the TileJSON spec.
   */
  "minzoom"?: number;
  /**
   * Maximum zoom level for which tiles are available, as in the TileJSON spec. Data from tiles at the maxzoom are used when displaying the map at higher zoom levels.
   *
   * @default
   * ```json
   * 22
   * ```
   */
  "maxzoom"?: number;
  /**
   * The minimum visual size to display tiles for this layer. Only configurable for raster layers.
   *
   * @default
   * ```json
   * 512
   * ```
   */
  "tileSize"?: number;
  /**
   * Contains an attribution to be displayed when the map is shown to a user.
   */
  "attribution"?: string;
  /**
   * The encoding used by this source. Mapbox Terrain RGB is used by default.
   *
   * @default
   * ```json
   * "mapbox"
   * ```
   */
  "encoding"?: "terrarium" | "mapbox" | "custom";
  /**
   * Value that will be multiplied by the red channel value when decoding. Only used on custom encodings.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "redFactor"?: number;
  /**
   * Value that will be multiplied by the blue channel value when decoding. Only used on custom encodings.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "blueFactor"?: number;
  /**
   * Value that will be multiplied by the green channel value when decoding. Only used on custom encodings.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "greenFactor"?: number;
  /**
   * Value that will be added to the encoding mix when decoding. Only used on custom encodings.
   */
  "baseShift"?: number;
  /**
   * A setting to determine whether a source's tiles are cached locally.
   */
  "volatile"?: boolean;
};
type GeoJSONSourceSpecification = {
  /**
   * The data type of the GeoJSON source.
   */
  "type": "geojson";
  /**
   * A URL to a GeoJSON file, or inline GeoJSON.
   */
  "data": GeoJSON.GeoJSON | string;
  /**
   * Maximum zoom level at which to create vector tiles (higher means greater detail at high zoom levels).
   *
   * @default
   * ```json
   * 18
   * ```
   */
  "maxzoom"?: number;
  /**
   * Contains an attribution to be displayed when the map is shown to a user.
   */
  "attribution"?: string;
  /**
   * Size of the tile buffer on each side. A value of 0 produces no buffer. A value of 512 produces a buffer as wide as the tile itself. Larger values produce fewer rendering artifacts near tile edges and slower performance.
   *
   * @default
   * ```json
   * 128
   * ```
   */
  "buffer"?: number;
  /**
   * An expression for filtering features prior to processing them for rendering.
   */
  "filter"?: FilterSpecification;
  /**
   * Douglas-Peucker simplification tolerance (higher means simpler geometries and faster performance).
   *
   * @default
   * ```json
   * 0.375
   * ```
   */
  "tolerance"?: number;
  /**
   * If the data is a collection of point features, setting this to true clusters the points by radius into groups. Cluster groups become new `Point` features in the source with additional properties:
   *
   *  * `cluster` Is `true` if the point is a cluster
   *
   *  * `cluster_id` A unique id for the cluster to be used in conjunction with the [cluster inspection methods](https://maplibre.org/maplibre-gl-js/docs/API/classes/GeoJSONSource/#getclusterexpansionzoom)
   *
   *  * `point_count` Number of original points grouped into this cluster
   *
   *  * `point_count_abbreviated` An abbreviated point count
   */
  "cluster"?: boolean;
  /**
   * Radius of each cluster if clustering is enabled. A value of 512 indicates a radius equal to the width of a tile.
   *
   * @default
   * ```json
   * 50
   * ```
   */
  "clusterRadius"?: number;
  /**
   * Max zoom on which to cluster points if clustering is enabled. Defaults to one zoom less than maxzoom (so that last zoom features are not clustered). Clusters are re-evaluated at integer zoom levels so setting clusterMaxZoom to 14 means the clusters will be displayed until z15.
   */
  "clusterMaxZoom"?: number;
  /**
   * Minimum number of points necessary to form a cluster if clustering is enabled. Defaults to `2`.
   */
  "clusterMinPoints"?: number;
  /**
   * An object defining custom properties on the generated clusters if clustering is enabled, aggregating values from clustered points. Has the form `{"property_name": [operator, map_expression]}`. `operator` is any expression function that accepts at least 2 operands (e.g. `"+"` or `"max"`) - it accumulates the property value from clusters/points the cluster contains; `map_expression` produces the value of a single point.
   *
   * Example: `{"sum": ["+", ["get", "scalerank"]]}`.
   *
   * For more advanced use cases, in place of `operator`, you can use a custom reduce expression that references a special `["accumulated"]` value, e.g.:
   *
   * `{"sum": [["+", ["accumulated"], ["get", "sum"]], ["get", "scalerank"]]}`
   */
  "clusterProperties"?: unknown;
  /**
   * Whether to calculate line distance metrics. This is required for line layers that specify `line-gradient` values.
   */
  "lineMetrics"?: boolean;
  /**
   * Whether to generate ids for the geojson features. When enabled, the `feature.id` property will be auto assigned based on its index in the `features` array, over-writing any previous values.
   */
  "generateId"?: boolean;
  /**
   * A property to use as a feature id (for feature state). Either a property name, or an object of the form `{<sourceLayer>: <propertyName>}`.
   */
  "promoteId"?: PromoteIdSpecification;
};
type VideoSourceSpecification = {
  /**
   * The data type of the video source.
   */
  "type": "video";
  /**
   * URLs to video content in order of preferred format.
   */
  "urls": Array<string>;
  /**
   * Corners of video specified in longitude, latitude pairs.
   */
  "coordinates": [[number, number], [number, number], [number, number], [number, number]];
};
type ImageSourceSpecification = {
  /**
   * The data type of the image source.
   */
  "type": "image";
  /**
   * URL that points to an image. Optional: a source created without a url starts empty and renders nothing until an image is set at runtime.
   */
  "url"?: string;
  /**
   * Corners of image specified in longitude, latitude pairs.
   */
  "coordinates": [[number, number], [number, number], [number, number], [number, number]];
};
type SourceSpecification = VectorSourceSpecification | RasterSourceSpecification | RasterDEMSourceSpecification | GeoJSONSourceSpecification | VideoSourceSpecification | ImageSourceSpecification;
type FillLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "fill";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
     */
    "fill-sort-key"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * Whether or not the fill should be antialiased.
     *
     * @default
     * ```json
     * true
     * ```
     */
    "fill-antialias"?: PropertyValueSpecification<boolean>;
    /**
     * The opacity of the entire fill layer. In contrast to the `fill-color`, this value will also affect the 1px stroke around the fill, if the stroke is used.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "fill-opacity"?: DataDrivenPropertyValueSpecification<number>;
    "fill-opacity-transition"?: TransitionSpecification;
    /**
     * Opacity applied to the layer as a whole. Unlike `fill-opacity` and alpha values in `fill-color`, which are applied per feature and accumulate where fills overlap, `fill-layer-opacity` is applied once so overlapping fills appear as a single surface at the given opacity. When both `fill-opacity` and `fill-layer-opacity` are set, the per-feature, overlap accumulation is preserved, then `fill-layer-opacity` composites the result. This property affects only the layer it is set on and cannot be used to composite multiple layers together or control how this layer blends with layers above or below it.
     *
     * ![fill-opacity vs. fill-layer-opacity](assets/fill-layer-opacity.svg)
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "fill-layer-opacity"?: PropertyValueSpecification<number>;
    "fill-layer-opacity-transition"?: TransitionSpecification;
    /**
     * The color of the filled part of this layer. This color can be specified as `rgba` with an alpha component and the color's opacity will not affect the opacity of the 1px stroke, if it is used. When used with an SDF fill pattern, this serves as the foreground color of the pattern.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "fill-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "fill-color-transition"?: TransitionSpecification;
    /**
     * The outline color of the fill. Matches the value of `fill-color` if unspecified.
     */
    "fill-outline-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "fill-outline-color-transition"?: TransitionSpecification;
    /**
     * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
     *
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "fill-translate"?: PropertyValueSpecification<[number, number]>;
    "fill-translate-transition"?: TransitionSpecification;
    /**
     * Controls the frame of reference for `fill-translate`.
     *
     * @default
     * ```json
     * "map"
     * ```
     */
    "fill-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
    /**
     * Name of image in sprite to use for drawing image fills. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
     */
    "fill-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>;
    "fill-pattern-transition"?: TransitionSpecification;
  };
};
type LineLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "line";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * The display of line endings.
     *
     * @default
     * ```json
     * "butt"
     * ```
     */
    "line-cap"?: DataDrivenPropertyValueSpecification<"butt" | "round" | "square">;
    /**
     * The display of lines when joining.
     *
     * @default
     * ```json
     * "miter"
     * ```
     */
    "line-join"?: DataDrivenPropertyValueSpecification<"bevel" | "round" | "miter">;
    /**
     * Used to automatically convert miter joins to bevel joins for sharp angles.
     *
     * @default
     * ```json
     * 2
     * ```
     */
    "line-miter-limit"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Used to automatically convert round joins to miter joins for shallow angles.
     *
     * @default
     * ```json
     * 1.05
     * ```
     */
    "line-round-limit"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
     */
    "line-sort-key"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * The opacity at which the line will be drawn.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "line-opacity"?: DataDrivenPropertyValueSpecification<number>;
    "line-opacity-transition"?: TransitionSpecification;
    /**
     * Opacity applied to the layer as a whole. Unlike `line-opacity` and alpha values in `line-color`, which are applied per feature and accumulate where lines overlap, `line-layer-opacity` is applied once so overlapping lines appear as a single surface at the given opacity. When both `line-opacity` and `line-layer-opacity` are set, the per-feature, overlap accumulation is preserved, then layer-opacity composites the result. This property affects only the layer it is set on and cannot be used to composite multiple layers together or control how this layer blends with layers above or below it.
     *
     * ![line-opacity vs. line-layer-opacity](assets/line-layer-opacity.svg)
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "line-layer-opacity"?: PropertyValueSpecification<number>;
    "line-layer-opacity-transition"?: TransitionSpecification;
    /**
     * The color with which the line will be drawn.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "line-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "line-color-transition"?: TransitionSpecification;
    /**
     * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
     *
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "line-translate"?: PropertyValueSpecification<[number, number]>;
    "line-translate-transition"?: TransitionSpecification;
    /**
     * Controls the frame of reference for `line-translate`.
     *
     * @default
     * ```json
     * "map"
     * ```
     */
    "line-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
    /**
     * Stroke thickness.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "line-width"?: DataDrivenPropertyValueSpecification<number>;
    "line-width-transition"?: TransitionSpecification;
    /**
     * Draws a line casing outside of a line's actual path. Value indicates the width of the inner gap.
     */
    "line-gap-width"?: DataDrivenPropertyValueSpecification<number>;
    "line-gap-width-transition"?: TransitionSpecification;
    /**
     * The line's offset. For linear features, a positive value offsets the line to the right, relative to the direction of the line, and a negative value to the left. For polygon features, a positive value results in an inset, and a negative value results in an outset.
     */
    "line-offset"?: DataDrivenPropertyValueSpecification<number>;
    "line-offset-transition"?: TransitionSpecification;
    /**
     * Blur applied to the line, in pixels.
     */
    "line-blur"?: DataDrivenPropertyValueSpecification<number>;
    "line-blur-transition"?: TransitionSpecification;
    /**
     * Specifies the lengths of the alternating dashes and gaps that form the dash pattern. The lengths are later scaled by the line width. To convert a dash length to pixels, multiply the length by the current line width. GeoJSON sources with `lineMetrics: true` specified won't render dashed lines to the expected scale. Zoom-dependent expressions will be evaluated only at integer zoom levels. The only way to create an array value is using `["literal", [...]]`; arrays cannot be read from or derived from feature properties.
     */
    "line-dasharray"?: DataDrivenPropertyValueSpecification<Array<number>>;
    "line-dasharray-transition"?: TransitionSpecification;
    /**
     * Name of image in sprite to use for drawing image lines. For seamless patterns, image width must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
     */
    "line-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>;
    "line-pattern-transition"?: TransitionSpecification;
    /**
     * Defines a gradient with which to color a line feature. Can only be used with GeoJSON sources that specify `"lineMetrics": true`.
     */
    "line-gradient"?: ExpressionSpecification;
  };
};
type SymbolLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "symbol";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Label placement relative to its geometry.
     *
     * @default
     * ```json
     * "point"
     * ```
     */
    "symbol-placement"?: PropertyValueSpecification<"point" | "line" | "line-center">;
    /**
     * Distance between two symbol anchors.
     *
     * @default
     * ```json
     * 250
     * ```
     */
    "symbol-spacing"?: PropertyValueSpecification<number>;
    /**
     * If true, the symbols will not cross tile edges to avoid mutual collisions. Recommended in layers that don't have enough padding in the vector tile to prevent collisions, or if it is a point symbol layer placed after a line symbol layer. When using a client that supports global collision detection, like MapLibre GL JS version 0.42.0 or greater, enabling this property is not needed to prevent clipped labels at tile boundaries.
     */
    "symbol-avoid-edges"?: PropertyValueSpecification<boolean>;
    /**
     * Sorts features in ascending order based on this value. Features with lower sort keys are drawn and placed first.  When `icon-allow-overlap` or `text-allow-overlap` is `false`, features with a lower sort key will have priority during placement. When `icon-allow-overlap` or `text-allow-overlap` is set to `true`, features with a higher sort key will overlap over features with a lower sort key.
     */
    "symbol-sort-key"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Determines whether overlapping symbols in the same layer are rendered in the order that they appear in the data source or by their y-position relative to the viewport. To control the order and prioritization of symbols otherwise, use `symbol-sort-key`.
     *
     * @default
     * ```json
     * "auto"
     * ```
     */
    "symbol-z-order"?: PropertyValueSpecification<"auto" | "viewport-y" | "source">;
    /**
     * If true, the icon will be visible even if it collides with other previously drawn symbols.
     */
    "icon-allow-overlap"?: PropertyValueSpecification<boolean>;
    /**
     * Allows for control over whether to show an icon when it overlaps other symbols on the map. If `icon-overlap` is not set, `icon-allow-overlap` is used instead.
     */
    "icon-overlap"?: PropertyValueSpecification<"never" | "always" | "cooperative">;
    /**
     * If true, other symbols can be visible even if they collide with the icon.
     */
    "icon-ignore-placement"?: PropertyValueSpecification<boolean>;
    /**
     * If true, text will display without their corresponding icons when the icon collides with other symbols and the text does not.
     */
    "icon-optional"?: PropertyValueSpecification<boolean>;
    /**
     * In combination with `symbol-placement`, determines the rotation behavior of icons.
     *
     * @default
     * ```json
     * "auto"
     * ```
     */
    "icon-rotation-alignment"?: DataDrivenPropertyValueSpecification<"map" | "viewport" | "auto">;
    /**
     * Scales the original size of the icon by the provided factor. The new pixel size of the image will be the original pixel size multiplied by `icon-size`. 1 is the original size; 3 triples the size of the image.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "icon-size"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Scales the icon to fit around the associated text.
     *
     * @default
     * ```json
     * "none"
     * ```
     */
    "icon-text-fit"?: PropertyValueSpecification<"none" | "width" | "height" | "both">;
    /**
     * Size of the additional area added to dimensions determined by `icon-text-fit`, in clockwise order: top, right, bottom, left.
     *
     * @default
     * ```json
     * [0, 0, 0, 0]
     * ```
     */
    "icon-text-fit-padding"?: PropertyValueSpecification<[number, number, number, number]>;
    /**
     * Name of image in sprite to use for drawing an image background.
     */
    "icon-image"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>;
    /**
     * Rotates the icon clockwise.
     */
    "icon-rotate"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Size of additional area round the icon bounding box used for detecting symbol collisions.
     *
     * @default
     * ```json
     * [2]
     * ```
     */
    "icon-padding"?: DataDrivenPropertyValueSpecification<PaddingSpecification>;
    /**
     * If true, the icon may be flipped to prevent it from being rendered upside-down.
     */
    "icon-keep-upright"?: PropertyValueSpecification<boolean>;
    /**
     * Offset distance of icon from its anchor. Positive values indicate right and down, while negative values indicate left and up. Each component is multiplied by the value of `icon-size` to obtain the final offset in pixels. When combined with `icon-rotate` the offset will be as if the rotated direction was up.
     *
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "icon-offset"?: DataDrivenPropertyValueSpecification<[number, number]>;
    /**
     * Part of the icon placed closest to the anchor.
     *
     * @default
     * ```json
     * "center"
     * ```
     */
    "icon-anchor"?: DataDrivenPropertyValueSpecification<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">;
    /**
     * Orientation of icon when map is pitched.
     *
     * @default
     * ```json
     * "auto"
     * ```
     */
    "icon-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport" | "auto">;
    /**
     * Orientation of text when map is pitched.
     *
     * @default
     * ```json
     * "auto"
     * ```
     */
    "text-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport" | "auto">;
    /**
     * In combination with `symbol-placement`, determines the rotation behavior of the individual glyphs forming the text.
     *
     * @default
     * ```json
     * "auto"
     * ```
     */
    "text-rotation-alignment"?: PropertyValueSpecification<"map" | "viewport" | "viewport-glyph" | "auto">;
    /**
     * Value to use for a text label. If a plain `string` is provided, it will be treated as a `formatted` with default/inherited formatting options.
     */
    "text-field"?: DataDrivenPropertyValueSpecification<FormattedSpecification>;
    /**
     * Fonts to use for displaying text. If the `glyphs` root property is specified, this array is joined together and interpreted as a font stack name. Otherwise, it is interpreted as a cascading fallback list of local font names.
     *
     * @default
     * ```json
     * ["Open Sans Regular", "Arial Unicode MS Regular"]
     * ```
     */
    "text-font"?: DataDrivenPropertyValueSpecification<Array<string>>;
    /**
     * Font size.
     *
     * @default
     * ```json
     * 16
     * ```
     */
    "text-size"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * The maximum line width for text wrapping.
     *
     * @default
     * ```json
     * 10
     * ```
     */
    "text-max-width"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Text leading value for multi-line text.
     *
     * @default
     * ```json
     * 1.2
     * ```
     */
    "text-line-height"?: PropertyValueSpecification<number>;
    /**
     * Text tracking amount.
     */
    "text-letter-spacing"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Text justification options.
     *
     * @default
     * ```json
     * "center"
     * ```
     */
    "text-justify"?: DataDrivenPropertyValueSpecification<"auto" | "left" | "center" | "right">;
    /**
     * Radial offset of text, in the direction of the symbol's anchor. Useful in combination with `text-variable-anchor`, which defaults to using the two-dimensional `text-offset` if present.
     */
    "text-radial-offset"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * To increase the chance of placing high-priority labels on the map, you can provide an array of `text-anchor` locations: the renderer will attempt to place the label at each location, in order, before moving onto the next label. Use `text-justify: auto` to choose justification based on anchor position. To apply an offset, use the `text-radial-offset` or the two-dimensional `text-offset`.
     *
     * @example
     * ```json
     * ["center", "left", "right"]
     * ```
     */
    "text-variable-anchor"?: PropertyValueSpecification<Array<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">>;
    /**
     * To increase the chance of placing high-priority labels on the map, you can provide an array of `text-anchor` locations, each paired with an offset value. The renderer will attempt to place the label at each location, in order, before moving on to the next location+offset. Use `text-justify: auto` to choose justification based on anchor position.
     *
     *  The length of the array must be even, and must alternate between enum and point entries. i.e., each anchor location must be accompanied by a point, and that point defines the offset when the corresponding anchor location is used. Positive offset values indicate right and down, while negative values indicate left and up. Anchor locations may repeat, allowing the renderer to try multiple offsets to try and place a label using the same anchor.
     *
     *  When present, this property takes precedence over `text-anchor`, `text-variable-anchor`, `text-offset`, and `text-radial-offset`.
     *
     *  ```json
     *
     *  { "text-variable-anchor-offset": ["top", [0, 4], "left", [3,0], "bottom", [1, 1]] }
     *
     *  ```
     *
     *  When the renderer chooses the `top` anchor, `[0, 4]` will be used for `text-offset`; the text will be shifted down by 4 ems.
     *
     *  When the renderer chooses the `left` anchor, `[3, 0]` will be used for `text-offset`; the text will be shifted right by 3 ems.
     *
     * @example
     * ```json
     * ["top", [0, 4], "left", [3, 0], "bottom", [1, 1]]
     * ```
     */
    "text-variable-anchor-offset"?: DataDrivenPropertyValueSpecification<VariableAnchorOffsetCollectionSpecification>;
    /**
     * Part of the text placed closest to the anchor.
     *
     * @default
     * ```json
     * "center"
     * ```
     */
    "text-anchor"?: DataDrivenPropertyValueSpecification<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">;
    /**
     * Maximum angle change between adjacent characters.
     *
     * @default
     * ```json
     * 45
     * ```
     */
    "text-max-angle"?: PropertyValueSpecification<number>;
    /**
     * The property allows control over a symbol's orientation. Note that the property values act as a hint, so that a symbol whose language doesn’t support the provided orientation will be laid out in its natural orientation. Example: English point symbol will be rendered horizontally even if array value contains single 'vertical' enum value. The order of elements in an array define priority order for the placement of an orientation variant.
     */
    "text-writing-mode"?: PropertyValueSpecification<Array<"horizontal" | "vertical">>;
    /**
     * Rotates the text clockwise.
     */
    "text-rotate"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Size of the additional area around the text bounding box used for detecting symbol collisions.
     *
     * @default
     * ```json
     * 2
     * ```
     */
    "text-padding"?: PropertyValueSpecification<number>;
    /**
     * If true, the text may be flipped vertically to prevent it from being rendered upside-down.
     *
     * @default
     * ```json
     * true
     * ```
     */
    "text-keep-upright"?: PropertyValueSpecification<boolean>;
    /**
     * Specifies how to capitalize text, similar to the CSS `text-transform` property.
     *
     * @default
     * ```json
     * "none"
     * ```
     */
    "text-transform"?: DataDrivenPropertyValueSpecification<"none" | "uppercase" | "lowercase">;
    /**
     * Offset distance of text from its anchor. Positive values indicate right and down, while negative values indicate left and up. If used with text-variable-anchor, input values will be taken as absolute values. Offsets along the x- and y-axis will be applied automatically based on the anchor position.
     *
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "text-offset"?: DataDrivenPropertyValueSpecification<[number, number]>;
    /**
     * If true, the text will be visible even if it collides with other previously drawn symbols.
     */
    "text-allow-overlap"?: PropertyValueSpecification<boolean>;
    /**
     * Allows for control over whether to show symbol text when it overlaps other symbols on the map. If `text-overlap` is not set, `text-allow-overlap` is used instead
     */
    "text-overlap"?: PropertyValueSpecification<"never" | "always" | "cooperative">;
    /**
     * If true, other symbols can be visible even if they collide with the text.
     */
    "text-ignore-placement"?: PropertyValueSpecification<boolean>;
    /**
     * If true, icons will display without their corresponding text when the text collides with other symbols and the icon does not.
     */
    "text-optional"?: PropertyValueSpecification<boolean>;
    /**
     * The height above the anchor, in meters, at which the symbol is placed. Use `symbol-height-anchor` to control what this height is measured from.
     */
    "symbol-height-offset"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Defines what `symbol-height-offset` is measured from.
     *
     * @default
     * ```json
     * "ground"
     * ```
     */
    "symbol-height-anchor"?: PropertyValueSpecification<"ground" | "absolute">;
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * The opacity at which the icon will be drawn.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "icon-opacity"?: DataDrivenPropertyValueSpecification<number>;
    "icon-opacity-transition"?: TransitionSpecification;
    /**
     * The color of the icon. This can only be used with SDF icons.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "icon-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "icon-color-transition"?: TransitionSpecification;
    /**
     * The color of the icon's halo. Icon halos can only be used with SDF icons.
     *
     * @default
     * ```json
     * "rgba(0, 0, 0, 0)"
     * ```
     */
    "icon-halo-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "icon-halo-color-transition"?: TransitionSpecification;
    /**
     * Distance of halo to the icon outline.
     *
     * The unit is in pixels only for SDF sprites that were created with a blur radius of 8, multiplied by the display density. I.e., the radius needs to be 16 for `@2x` sprites, etc.
     */
    "icon-halo-width"?: DataDrivenPropertyValueSpecification<number>;
    "icon-halo-width-transition"?: TransitionSpecification;
    /**
     * Fade out the halo towards the outside.
     */
    "icon-halo-blur"?: DataDrivenPropertyValueSpecification<number>;
    "icon-halo-blur-transition"?: TransitionSpecification;
    /**
     * Distance that the icon's anchor is moved from its original placement. Positive values indicate right and down, while negative values indicate left and up.
     *
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "icon-translate"?: PropertyValueSpecification<[number, number]>;
    "icon-translate-transition"?: TransitionSpecification;
    /**
     * Controls the frame of reference for `icon-translate`.
     *
     * @default
     * ```json
     * "map"
     * ```
     */
    "icon-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
    /**
     * The opacity at which the text will be drawn.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "text-opacity"?: DataDrivenPropertyValueSpecification<number>;
    "text-opacity-transition"?: TransitionSpecification;
    /**
     * The color with which the text will be drawn.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "text-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "text-color-transition"?: TransitionSpecification;
    /**
     * The color of the text's halo, which helps it stand out from backgrounds.
     *
     * @default
     * ```json
     * "rgba(0, 0, 0, 0)"
     * ```
     */
    "text-halo-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "text-halo-color-transition"?: TransitionSpecification;
    /**
     * Distance of halo to the font outline. Max text halo width is 1/4 of the font-size.
     */
    "text-halo-width"?: DataDrivenPropertyValueSpecification<number>;
    "text-halo-width-transition"?: TransitionSpecification;
    /**
     * The halo's fadeout distance towards the outside.
     */
    "text-halo-blur"?: DataDrivenPropertyValueSpecification<number>;
    "text-halo-blur-transition"?: TransitionSpecification;
    /**
     * Distance that the text's anchor is moved from its original placement. Positive values indicate right and down, while negative values indicate left and up.
     *
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "text-translate"?: PropertyValueSpecification<[number, number]>;
    "text-translate-transition"?: TransitionSpecification;
    /**
     * Controls the frame of reference for `text-translate`.
     *
     * @default
     * ```json
     * "map"
     * ```
     */
    "text-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
  };
};
type CircleLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "circle";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
     */
    "circle-sort-key"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * Circle radius.
     *
     * @default
     * ```json
     * 5
     * ```
     */
    "circle-radius"?: DataDrivenPropertyValueSpecification<number>;
    "circle-radius-transition"?: TransitionSpecification;
    /**
     * The fill color of the circle.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "circle-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "circle-color-transition"?: TransitionSpecification;
    /**
     * Amount to blur the circle. 1 blurs the circle such that only the centerpoint is full opacity.
     */
    "circle-blur"?: DataDrivenPropertyValueSpecification<number>;
    "circle-blur-transition"?: TransitionSpecification;
    /**
     * The opacity at which the circle will be drawn.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "circle-opacity"?: DataDrivenPropertyValueSpecification<number>;
    "circle-opacity-transition"?: TransitionSpecification;
    /**
     * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
     *
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "circle-translate"?: PropertyValueSpecification<[number, number]>;
    "circle-translate-transition"?: TransitionSpecification;
    /**
     * Controls the frame of reference for `circle-translate`.
     *
     * @default
     * ```json
     * "map"
     * ```
     */
    "circle-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
    /**
     * Controls the scaling behavior of the circle when the map is pitched.
     *
     * @default
     * ```json
     * "map"
     * ```
     */
    "circle-pitch-scale"?: PropertyValueSpecification<"map" | "viewport">;
    /**
     * Orientation of circle when map is pitched.
     *
     * @default
     * ```json
     * "viewport"
     * ```
     */
    "circle-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport">;
    /**
     * The width of the circle's stroke. Strokes are placed outside of the `circle-radius`.
     */
    "circle-stroke-width"?: DataDrivenPropertyValueSpecification<number>;
    "circle-stroke-width-transition"?: TransitionSpecification;
    /**
     * The stroke color of the circle.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "circle-stroke-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "circle-stroke-color-transition"?: TransitionSpecification;
    /**
     * The opacity of the circle's stroke.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "circle-stroke-opacity"?: DataDrivenPropertyValueSpecification<number>;
    "circle-stroke-opacity-transition"?: TransitionSpecification;
  };
};
type HeatmapLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "heatmap";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * Radius of influence of one heatmap point in pixels. Increasing the value makes the heatmap smoother, but less detailed.
     *
     * @default
     * ```json
     * 30
     * ```
     */
    "heatmap-radius"?: DataDrivenPropertyValueSpecification<number>;
    "heatmap-radius-transition"?: TransitionSpecification;
    /**
     * A measure of how much an individual point contributes to the heatmap. A value of 10 would be equivalent to having 10 points of weight 1 in the same spot. Especially useful when combined with clustering.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "heatmap-weight"?: DataDrivenPropertyValueSpecification<number>;
    /**
     * Similar to `heatmap-weight` but controls the intensity of the heatmap globally. Primarily used for adjusting the heatmap based on zoom level.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "heatmap-intensity"?: PropertyValueSpecification<number>;
    "heatmap-intensity-transition"?: TransitionSpecification;
    /**
     * Defines the color of each pixel based on its density value in a heatmap.  Should be an expression that uses `["heatmap-density"]` as input.
     *
     * @default
     * ```json
     * [
     *     "interpolate",
     *     ["linear"],
     *     ["heatmap-density"],
     *     0,
     *     "rgba(0, 0, 255, 0)",
     *     0.1,
     *     "royalblue",
     *     0.3,
     *     "cyan",
     *     0.5,
     *     "lime",
     *     0.7,
     *     "yellow",
     *     1,
     *     "red"
     * ]
     * ```
     */
    "heatmap-color"?: ExpressionSpecification;
    /**
     * The global opacity at which the heatmap layer will be drawn.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "heatmap-opacity"?: PropertyValueSpecification<number>;
    "heatmap-opacity-transition"?: TransitionSpecification;
  };
};
type FillExtrusionLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "fill-extrusion";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
    /**
     * The distance from each fill extrusion corner, measured along the adjacent edges, that is replaced by a rounded corner. A value of `0` disables rounded corners.
     */
    "fill-extrusion-rounded-corner-distance"?: number;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * The opacity of the entire fill extrusion layer. This is rendered on a per-layer, not per-feature, basis, and data-driven styling is not available.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "fill-extrusion-opacity"?: PropertyValueSpecification<number>;
    "fill-extrusion-opacity-transition"?: TransitionSpecification;
    /**
     * The base color of the extruded fill. The extrusion's surfaces will be shaded differently based on this color in combination with the root `light` settings. If this color is specified as `rgba` with an alpha component, the alpha component will be ignored; use `fill-extrusion-opacity` to set layer opacity.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "fill-extrusion-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
    "fill-extrusion-color-transition"?: TransitionSpecification;
    /**
     * The geometry's offset. Values are `[x, y]` where negatives indicate left and up (on the flat plane), respectively.
     *
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "fill-extrusion-translate"?: PropertyValueSpecification<[number, number]>;
    "fill-extrusion-translate-transition"?: TransitionSpecification;
    /**
     * Controls the frame of reference for `fill-extrusion-translate`.
     *
     * @default
     * ```json
     * "map"
     * ```
     */
    "fill-extrusion-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
    /**
     * Name of image in sprite to use for drawing images on extruded fills. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
     */
    "fill-extrusion-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>;
    "fill-extrusion-pattern-transition"?: TransitionSpecification;
    /**
     * The height with which to extrude this layer. Negative values extrude below ground level, so a floor that is entirely underground can be expressed.
     */
    "fill-extrusion-height"?: DataDrivenPropertyValueSpecification<number>;
    "fill-extrusion-height-transition"?: TransitionSpecification;
    /**
     * The height with which to extrude the base of this layer. Must be less than or equal to `fill-extrusion-height`. Negative values extrude below ground level, e.g. underground floors.
     */
    "fill-extrusion-base"?: DataDrivenPropertyValueSpecification<number>;
    "fill-extrusion-base-transition"?: TransitionSpecification;
    /**
     * Whether to apply a vertical gradient to the sides of a fill-extrusion layer. If true, sides will be shaded slightly darker farther down.
     *
     * @default
     * ```json
     * true
     * ```
     */
    "fill-extrusion-vertical-gradient"?: PropertyValueSpecification<boolean>;
  };
};
type RasterLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "raster";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * The opacity at which the image will be drawn.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "raster-opacity"?: PropertyValueSpecification<number>;
    "raster-opacity-transition"?: TransitionSpecification;
    /**
     * Rotates hues around the color wheel.
     */
    "raster-hue-rotate"?: PropertyValueSpecification<number>;
    "raster-hue-rotate-transition"?: TransitionSpecification;
    /**
     * Increase or reduce the brightness of the image. The value is the minimum brightness.
     */
    "raster-brightness-min"?: PropertyValueSpecification<number>;
    "raster-brightness-min-transition"?: TransitionSpecification;
    /**
     * Increase or reduce the brightness of the image. The value is the maximum brightness.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "raster-brightness-max"?: PropertyValueSpecification<number>;
    "raster-brightness-max-transition"?: TransitionSpecification;
    /**
     * Increase or reduce the saturation of the image.
     */
    "raster-saturation"?: PropertyValueSpecification<number>;
    "raster-saturation-transition"?: TransitionSpecification;
    /**
     * Increase or reduce the contrast of the image.
     */
    "raster-contrast"?: PropertyValueSpecification<number>;
    "raster-contrast-transition"?: TransitionSpecification;
    /**
     * The resampling/interpolation method to use for overscaling, also known as texture magnification filter.
     * ![Visual comparison of linear resampling versus nearest resampling](assets/resampling.png)
     *
     * @default
     * ```json
     * "linear"
     * ```
     */
    "resampling"?: PropertyValueSpecification<"linear" | "nearest">;
    /**
     * The resampling/interpolation method to use for overscaling, also known as texture magnification filter. It is advised to use the generic `resampling` paint property instead.
     *
     * @default
     * ```json
     * "linear"
     * ```
     */
    "raster-resampling"?: PropertyValueSpecification<"linear" | "nearest">;
    /**
     * Fade duration when a new tile is added, or when a video is started or its coordinates are updated.
     *
     * @default
     * ```json
     * 300
     * ```
     */
    "raster-fade-duration"?: PropertyValueSpecification<number>;
  };
};
type HillshadeLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "hillshade";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * The direction of the light source(s) used to generate the hillshading with 0 as the top of the viewport if `hillshade-illumination-anchor` is set to `viewport` and due north if `hillshade-illumination-anchor` is set to `map`. Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
     *
     * @default
     * ```json
     * 335
     * ```
     */
    "hillshade-illumination-direction"?: PropertyValueSpecification<NumberArraySpecification>;
    /**
     * The altitude of the light source(s) used to generate the hillshading with 0 as sunset and 90 as noon. Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
     *
     * @default
     * ```json
     * 45
     * ```
     */
    "hillshade-illumination-altitude"?: PropertyValueSpecification<NumberArraySpecification>;
    /**
     * Direction of light source when map is rotated.
     *
     * @default
     * ```json
     * "viewport"
     * ```
     */
    "hillshade-illumination-anchor"?: PropertyValueSpecification<"map" | "viewport">;
    /**
     * Intensity of the hillshade
     *
     * @default
     * ```json
     * 0.5
     * ```
     */
    "hillshade-exaggeration"?: PropertyValueSpecification<number>;
    "hillshade-exaggeration-transition"?: TransitionSpecification;
    /**
     * The shading color of areas that face away from the light source(s). Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "hillshade-shadow-color"?: PropertyValueSpecification<ColorArraySpecification>;
    "hillshade-shadow-color-transition"?: TransitionSpecification;
    /**
     * The shading color of areas that faces towards the light source(s). Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
     *
     * @default
     * ```json
     * "#FFFFFF"
     * ```
     */
    "hillshade-highlight-color"?: PropertyValueSpecification<ColorArraySpecification>;
    "hillshade-highlight-color-transition"?: TransitionSpecification;
    /**
     * The shading color used to accentuate rugged terrain like sharp cliffs and gorges.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "hillshade-accent-color"?: PropertyValueSpecification<ColorSpecification>;
    "hillshade-accent-color-transition"?: TransitionSpecification;
    /**
     * The hillshade algorithm to use, one of `standard`, `basic`, `combined`, `igor`, or `multidirectional`.
     * ![Visual comparison of standard, basic, igor, combined, and multidirectional hillshade-method](assets/hillshade_methods.png)
     *
     * @default
     * ```json
     * "standard"
     * ```
     */
    "hillshade-method"?: PropertyValueSpecification<"standard" | "basic" | "combined" | "igor" | "multidirectional">;
    /**
     * The resampling/interpolation method to use for overscaling, also known as texture magnification filter.
     * ![Visual comparison of linear resampling versus nearest resampling](assets/resampling.png)
     *
     * @default
     * ```json
     * "linear"
     * ```
     */
    "resampling"?: PropertyValueSpecification<"linear" | "nearest">;
  };
};
type ColorReliefLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "color-relief";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * Name of a source description to be used for this layer. Required for all layer types except `background`.
   */
  "source": string;
  /**
   * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
   */
  "source-layer"?: string;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
   */
  "filter"?: FilterSpecification;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * The opacity at which the color-relief will be drawn.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "color-relief-opacity"?: PropertyValueSpecification<number>;
    "color-relief-opacity-transition"?: TransitionSpecification;
    /**
     * Defines the color of each pixel based on its elevation. Should be an expression that uses `["elevation"]` as input.
     *
     * @example
     * ```json
     * [
     *     "interpolate",
     *     ["linear"],
     *     ["elevation"],
     *     0,
     *     "black",
     *     8849,
     *     "white"
     * ]
     * ```
     */
    "color-relief-color"?: ExpressionSpecification;
    /**
     * The resampling/interpolation method to use for overscaling, also known as texture magnification filter.
     * ![Visual comparison of linear resampling versus nearest resampling](assets/resampling.png)
     *
     * @default
     * ```json
     * "linear"
     * ```
     */
    "resampling"?: PropertyValueSpecification<"linear" | "nearest">;
  };
};
type BackgroundLayerSpecification = {
  /**
   * Unique layer name.
   */
  "id": string;
  "type": "background";
  /**
   * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
   *
   * @example
   * ```json
   * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
   * ```
   */
  "metadata"?: unknown;
  /**
   * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
   */
  "minzoom"?: number;
  /**
   * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
   */
  "maxzoom"?: number;
  /**
   * Layout properties for the layer.
   */
  "layout"?: {
    /**
     * Whether this layer is displayed.
     *
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification;
  };
  /**
   * Default paint properties for this layer.
   */
  "paint"?: {
    /**
     * The color with which the background will be drawn.
     *
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "background-color"?: PropertyValueSpecification<ColorSpecification>;
    "background-color-transition"?: TransitionSpecification;
    /**
     * Name of image in sprite to use for drawing an image background. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
     */
    "background-pattern"?: PropertyValueSpecification<ResolvedImageSpecification>;
    "background-pattern-transition"?: TransitionSpecification;
    /**
     * The opacity at which the background will be drawn.
     *
     * @default
     * ```json
     * 1
     * ```
     */
    "background-opacity"?: PropertyValueSpecification<number>;
    "background-opacity-transition"?: TransitionSpecification;
  };
};
type LayerSpecification = FillLayerSpecification | LineLayerSpecification | SymbolLayerSpecification | CircleLayerSpecification | HeatmapLayerSpecification | FillExtrusionLayerSpecification | RasterLayerSpecification | HillshadeLayerSpecification | ColorReliefLayerSpecification | BackgroundLayerSpecification;
/**
 * Union of all paint properties across all layer types.
 */
type AllPaintProperties = {
  /**
   * Whether or not the fill should be antialiased.
   *
   * @default
   * ```json
   * true
   * ```
   */
  "fill-antialias"?: PropertyValueSpecification<boolean>;
  /**
   * The opacity of the entire fill layer. In contrast to the `fill-color`, this value will also affect the 1px stroke around the fill, if the stroke is used.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "fill-opacity"?: DataDrivenPropertyValueSpecification<number>;
  "fill-opacity-transition"?: TransitionSpecification;
  /**
   * Opacity applied to the layer as a whole. Unlike `fill-opacity` and alpha values in `fill-color`, which are applied per feature and accumulate where fills overlap, `fill-layer-opacity` is applied once so overlapping fills appear as a single surface at the given opacity. When both `fill-opacity` and `fill-layer-opacity` are set, the per-feature, overlap accumulation is preserved, then `fill-layer-opacity` composites the result. This property affects only the layer it is set on and cannot be used to composite multiple layers together or control how this layer blends with layers above or below it.
   *
   * ![fill-opacity vs. fill-layer-opacity](assets/fill-layer-opacity.svg)
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "fill-layer-opacity"?: PropertyValueSpecification<number>;
  "fill-layer-opacity-transition"?: TransitionSpecification;
  /**
   * The color of the filled part of this layer. This color can be specified as `rgba` with an alpha component and the color's opacity will not affect the opacity of the 1px stroke, if it is used. When used with an SDF fill pattern, this serves as the foreground color of the pattern.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "fill-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "fill-color-transition"?: TransitionSpecification;
  /**
   * The outline color of the fill. Matches the value of `fill-color` if unspecified.
   */
  "fill-outline-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "fill-outline-color-transition"?: TransitionSpecification;
  /**
   * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
   *
   * @default
   * ```json
   * [0, 0]
   * ```
   */
  "fill-translate"?: PropertyValueSpecification<[number, number]>;
  "fill-translate-transition"?: TransitionSpecification;
  /**
   * Controls the frame of reference for `fill-translate`.
   *
   * @default
   * ```json
   * "map"
   * ```
   */
  "fill-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * Name of image in sprite to use for drawing image fills. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
   */
  "fill-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>;
  "fill-pattern-transition"?: TransitionSpecification;
  /**
   * The opacity at which the line will be drawn.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "line-opacity"?: DataDrivenPropertyValueSpecification<number>;
  "line-opacity-transition"?: TransitionSpecification;
  /**
   * Opacity applied to the layer as a whole. Unlike `line-opacity` and alpha values in `line-color`, which are applied per feature and accumulate where lines overlap, `line-layer-opacity` is applied once so overlapping lines appear as a single surface at the given opacity. When both `line-opacity` and `line-layer-opacity` are set, the per-feature, overlap accumulation is preserved, then layer-opacity composites the result. This property affects only the layer it is set on and cannot be used to composite multiple layers together or control how this layer blends with layers above or below it.
   *
   * ![line-opacity vs. line-layer-opacity](assets/line-layer-opacity.svg)
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "line-layer-opacity"?: PropertyValueSpecification<number>;
  "line-layer-opacity-transition"?: TransitionSpecification;
  /**
   * The color with which the line will be drawn.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "line-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "line-color-transition"?: TransitionSpecification;
  /**
   * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
   *
   * @default
   * ```json
   * [0, 0]
   * ```
   */
  "line-translate"?: PropertyValueSpecification<[number, number]>;
  "line-translate-transition"?: TransitionSpecification;
  /**
   * Controls the frame of reference for `line-translate`.
   *
   * @default
   * ```json
   * "map"
   * ```
   */
  "line-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * Stroke thickness.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "line-width"?: DataDrivenPropertyValueSpecification<number>;
  "line-width-transition"?: TransitionSpecification;
  /**
   * Draws a line casing outside of a line's actual path. Value indicates the width of the inner gap.
   */
  "line-gap-width"?: DataDrivenPropertyValueSpecification<number>;
  "line-gap-width-transition"?: TransitionSpecification;
  /**
   * The line's offset. For linear features, a positive value offsets the line to the right, relative to the direction of the line, and a negative value to the left. For polygon features, a positive value results in an inset, and a negative value results in an outset.
   */
  "line-offset"?: DataDrivenPropertyValueSpecification<number>;
  "line-offset-transition"?: TransitionSpecification;
  /**
   * Blur applied to the line, in pixels.
   */
  "line-blur"?: DataDrivenPropertyValueSpecification<number>;
  "line-blur-transition"?: TransitionSpecification;
  /**
   * Specifies the lengths of the alternating dashes and gaps that form the dash pattern. The lengths are later scaled by the line width. To convert a dash length to pixels, multiply the length by the current line width. GeoJSON sources with `lineMetrics: true` specified won't render dashed lines to the expected scale. Zoom-dependent expressions will be evaluated only at integer zoom levels. The only way to create an array value is using `["literal", [...]]`; arrays cannot be read from or derived from feature properties.
   */
  "line-dasharray"?: DataDrivenPropertyValueSpecification<Array<number>>;
  "line-dasharray-transition"?: TransitionSpecification;
  /**
   * Name of image in sprite to use for drawing image lines. For seamless patterns, image width must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
   */
  "line-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>;
  "line-pattern-transition"?: TransitionSpecification;
  /**
   * Defines a gradient with which to color a line feature. Can only be used with GeoJSON sources that specify `"lineMetrics": true`.
   */
  "line-gradient"?: ExpressionSpecification;
  /**
   * The opacity at which the icon will be drawn.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "icon-opacity"?: DataDrivenPropertyValueSpecification<number>;
  "icon-opacity-transition"?: TransitionSpecification;
  /**
   * The color of the icon. This can only be used with SDF icons.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "icon-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "icon-color-transition"?: TransitionSpecification;
  /**
   * The color of the icon's halo. Icon halos can only be used with SDF icons.
   *
   * @default
   * ```json
   * "rgba(0, 0, 0, 0)"
   * ```
   */
  "icon-halo-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "icon-halo-color-transition"?: TransitionSpecification;
  /**
   * Distance of halo to the icon outline.
   *
   * The unit is in pixels only for SDF sprites that were created with a blur radius of 8, multiplied by the display density. I.e., the radius needs to be 16 for `@2x` sprites, etc.
   */
  "icon-halo-width"?: DataDrivenPropertyValueSpecification<number>;
  "icon-halo-width-transition"?: TransitionSpecification;
  /**
   * Fade out the halo towards the outside.
   */
  "icon-halo-blur"?: DataDrivenPropertyValueSpecification<number>;
  "icon-halo-blur-transition"?: TransitionSpecification;
  /**
   * Distance that the icon's anchor is moved from its original placement. Positive values indicate right and down, while negative values indicate left and up.
   *
   * @default
   * ```json
   * [0, 0]
   * ```
   */
  "icon-translate"?: PropertyValueSpecification<[number, number]>;
  "icon-translate-transition"?: TransitionSpecification;
  /**
   * Controls the frame of reference for `icon-translate`.
   *
   * @default
   * ```json
   * "map"
   * ```
   */
  "icon-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * The opacity at which the text will be drawn.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "text-opacity"?: DataDrivenPropertyValueSpecification<number>;
  "text-opacity-transition"?: TransitionSpecification;
  /**
   * The color with which the text will be drawn.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "text-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "text-color-transition"?: TransitionSpecification;
  /**
   * The color of the text's halo, which helps it stand out from backgrounds.
   *
   * @default
   * ```json
   * "rgba(0, 0, 0, 0)"
   * ```
   */
  "text-halo-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "text-halo-color-transition"?: TransitionSpecification;
  /**
   * Distance of halo to the font outline. Max text halo width is 1/4 of the font-size.
   */
  "text-halo-width"?: DataDrivenPropertyValueSpecification<number>;
  "text-halo-width-transition"?: TransitionSpecification;
  /**
   * The halo's fadeout distance towards the outside.
   */
  "text-halo-blur"?: DataDrivenPropertyValueSpecification<number>;
  "text-halo-blur-transition"?: TransitionSpecification;
  /**
   * Distance that the text's anchor is moved from its original placement. Positive values indicate right and down, while negative values indicate left and up.
   *
   * @default
   * ```json
   * [0, 0]
   * ```
   */
  "text-translate"?: PropertyValueSpecification<[number, number]>;
  "text-translate-transition"?: TransitionSpecification;
  /**
   * Controls the frame of reference for `text-translate`.
   *
   * @default
   * ```json
   * "map"
   * ```
   */
  "text-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * Circle radius.
   *
   * @default
   * ```json
   * 5
   * ```
   */
  "circle-radius"?: DataDrivenPropertyValueSpecification<number>;
  "circle-radius-transition"?: TransitionSpecification;
  /**
   * The fill color of the circle.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "circle-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "circle-color-transition"?: TransitionSpecification;
  /**
   * Amount to blur the circle. 1 blurs the circle such that only the centerpoint is full opacity.
   */
  "circle-blur"?: DataDrivenPropertyValueSpecification<number>;
  "circle-blur-transition"?: TransitionSpecification;
  /**
   * The opacity at which the circle will be drawn.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "circle-opacity"?: DataDrivenPropertyValueSpecification<number>;
  "circle-opacity-transition"?: TransitionSpecification;
  /**
   * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
   *
   * @default
   * ```json
   * [0, 0]
   * ```
   */
  "circle-translate"?: PropertyValueSpecification<[number, number]>;
  "circle-translate-transition"?: TransitionSpecification;
  /**
   * Controls the frame of reference for `circle-translate`.
   *
   * @default
   * ```json
   * "map"
   * ```
   */
  "circle-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * Controls the scaling behavior of the circle when the map is pitched.
   *
   * @default
   * ```json
   * "map"
   * ```
   */
  "circle-pitch-scale"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * Orientation of circle when map is pitched.
   *
   * @default
   * ```json
   * "viewport"
   * ```
   */
  "circle-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * The width of the circle's stroke. Strokes are placed outside of the `circle-radius`.
   */
  "circle-stroke-width"?: DataDrivenPropertyValueSpecification<number>;
  "circle-stroke-width-transition"?: TransitionSpecification;
  /**
   * The stroke color of the circle.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "circle-stroke-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "circle-stroke-color-transition"?: TransitionSpecification;
  /**
   * The opacity of the circle's stroke.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "circle-stroke-opacity"?: DataDrivenPropertyValueSpecification<number>;
  "circle-stroke-opacity-transition"?: TransitionSpecification;
  /**
   * Radius of influence of one heatmap point in pixels. Increasing the value makes the heatmap smoother, but less detailed.
   *
   * @default
   * ```json
   * 30
   * ```
   */
  "heatmap-radius"?: DataDrivenPropertyValueSpecification<number>;
  "heatmap-radius-transition"?: TransitionSpecification;
  /**
   * A measure of how much an individual point contributes to the heatmap. A value of 10 would be equivalent to having 10 points of weight 1 in the same spot. Especially useful when combined with clustering.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "heatmap-weight"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Similar to `heatmap-weight` but controls the intensity of the heatmap globally. Primarily used for adjusting the heatmap based on zoom level.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "heatmap-intensity"?: PropertyValueSpecification<number>;
  "heatmap-intensity-transition"?: TransitionSpecification;
  /**
   * Defines the color of each pixel based on its density value in a heatmap.  Should be an expression that uses `["heatmap-density"]` as input.
   *
   * @default
   * ```json
   * [
   *     "interpolate",
   *     ["linear"],
   *     ["heatmap-density"],
   *     0,
   *     "rgba(0, 0, 255, 0)",
   *     0.1,
   *     "royalblue",
   *     0.3,
   *     "cyan",
   *     0.5,
   *     "lime",
   *     0.7,
   *     "yellow",
   *     1,
   *     "red"
   * ]
   * ```
   */
  "heatmap-color"?: ExpressionSpecification;
  /**
   * The global opacity at which the heatmap layer will be drawn.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "heatmap-opacity"?: PropertyValueSpecification<number>;
  "heatmap-opacity-transition"?: TransitionSpecification;
  /**
   * The opacity of the entire fill extrusion layer. This is rendered on a per-layer, not per-feature, basis, and data-driven styling is not available.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "fill-extrusion-opacity"?: PropertyValueSpecification<number>;
  "fill-extrusion-opacity-transition"?: TransitionSpecification;
  /**
   * The base color of the extruded fill. The extrusion's surfaces will be shaded differently based on this color in combination with the root `light` settings. If this color is specified as `rgba` with an alpha component, the alpha component will be ignored; use `fill-extrusion-opacity` to set layer opacity.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "fill-extrusion-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>;
  "fill-extrusion-color-transition"?: TransitionSpecification;
  /**
   * The geometry's offset. Values are `[x, y]` where negatives indicate left and up (on the flat plane), respectively.
   *
   * @default
   * ```json
   * [0, 0]
   * ```
   */
  "fill-extrusion-translate"?: PropertyValueSpecification<[number, number]>;
  "fill-extrusion-translate-transition"?: TransitionSpecification;
  /**
   * Controls the frame of reference for `fill-extrusion-translate`.
   *
   * @default
   * ```json
   * "map"
   * ```
   */
  "fill-extrusion-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * Name of image in sprite to use for drawing images on extruded fills. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
   */
  "fill-extrusion-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>;
  "fill-extrusion-pattern-transition"?: TransitionSpecification;
  /**
   * The height with which to extrude this layer. Negative values extrude below ground level, so a floor that is entirely underground can be expressed.
   */
  "fill-extrusion-height"?: DataDrivenPropertyValueSpecification<number>;
  "fill-extrusion-height-transition"?: TransitionSpecification;
  /**
   * The height with which to extrude the base of this layer. Must be less than or equal to `fill-extrusion-height`. Negative values extrude below ground level, e.g. underground floors.
   */
  "fill-extrusion-base"?: DataDrivenPropertyValueSpecification<number>;
  "fill-extrusion-base-transition"?: TransitionSpecification;
  /**
   * Whether to apply a vertical gradient to the sides of a fill-extrusion layer. If true, sides will be shaded slightly darker farther down.
   *
   * @default
   * ```json
   * true
   * ```
   */
  "fill-extrusion-vertical-gradient"?: PropertyValueSpecification<boolean>;
  /**
   * The opacity at which the image will be drawn.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "raster-opacity"?: PropertyValueSpecification<number>;
  "raster-opacity-transition"?: TransitionSpecification;
  /**
   * Rotates hues around the color wheel.
   */
  "raster-hue-rotate"?: PropertyValueSpecification<number>;
  "raster-hue-rotate-transition"?: TransitionSpecification;
  /**
   * Increase or reduce the brightness of the image. The value is the minimum brightness.
   */
  "raster-brightness-min"?: PropertyValueSpecification<number>;
  "raster-brightness-min-transition"?: TransitionSpecification;
  /**
   * Increase or reduce the brightness of the image. The value is the maximum brightness.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "raster-brightness-max"?: PropertyValueSpecification<number>;
  "raster-brightness-max-transition"?: TransitionSpecification;
  /**
   * Increase or reduce the saturation of the image.
   */
  "raster-saturation"?: PropertyValueSpecification<number>;
  "raster-saturation-transition"?: TransitionSpecification;
  /**
   * Increase or reduce the contrast of the image.
   */
  "raster-contrast"?: PropertyValueSpecification<number>;
  "raster-contrast-transition"?: TransitionSpecification;
  /**
   * The resampling/interpolation method to use for overscaling, also known as texture magnification filter.
   * ![Visual comparison of linear resampling versus nearest resampling](assets/resampling.png)
   *
   * @default
   * ```json
   * "linear"
   * ```
   */
  "resampling"?: PropertyValueSpecification<"linear" | "nearest">;
  /**
   * The resampling/interpolation method to use for overscaling, also known as texture magnification filter. It is advised to use the generic `resampling` paint property instead.
   *
   * @default
   * ```json
   * "linear"
   * ```
   */
  "raster-resampling"?: PropertyValueSpecification<"linear" | "nearest">;
  /**
   * Fade duration when a new tile is added, or when a video is started or its coordinates are updated.
   *
   * @default
   * ```json
   * 300
   * ```
   */
  "raster-fade-duration"?: PropertyValueSpecification<number>;
  /**
   * The direction of the light source(s) used to generate the hillshading with 0 as the top of the viewport if `hillshade-illumination-anchor` is set to `viewport` and due north if `hillshade-illumination-anchor` is set to `map`. Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
   *
   * @default
   * ```json
   * 335
   * ```
   */
  "hillshade-illumination-direction"?: PropertyValueSpecification<NumberArraySpecification>;
  /**
   * The altitude of the light source(s) used to generate the hillshading with 0 as sunset and 90 as noon. Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
   *
   * @default
   * ```json
   * 45
   * ```
   */
  "hillshade-illumination-altitude"?: PropertyValueSpecification<NumberArraySpecification>;
  /**
   * Direction of light source when map is rotated.
   *
   * @default
   * ```json
   * "viewport"
   * ```
   */
  "hillshade-illumination-anchor"?: PropertyValueSpecification<"map" | "viewport">;
  /**
   * Intensity of the hillshade
   *
   * @default
   * ```json
   * 0.5
   * ```
   */
  "hillshade-exaggeration"?: PropertyValueSpecification<number>;
  "hillshade-exaggeration-transition"?: TransitionSpecification;
  /**
   * The shading color of areas that face away from the light source(s). Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "hillshade-shadow-color"?: PropertyValueSpecification<ColorArraySpecification>;
  "hillshade-shadow-color-transition"?: TransitionSpecification;
  /**
   * The shading color of areas that faces towards the light source(s). Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
   *
   * @default
   * ```json
   * "#FFFFFF"
   * ```
   */
  "hillshade-highlight-color"?: PropertyValueSpecification<ColorArraySpecification>;
  "hillshade-highlight-color-transition"?: TransitionSpecification;
  /**
   * The shading color used to accentuate rugged terrain like sharp cliffs and gorges.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "hillshade-accent-color"?: PropertyValueSpecification<ColorSpecification>;
  "hillshade-accent-color-transition"?: TransitionSpecification;
  /**
   * The hillshade algorithm to use, one of `standard`, `basic`, `combined`, `igor`, or `multidirectional`.
   * ![Visual comparison of standard, basic, igor, combined, and multidirectional hillshade-method](assets/hillshade_methods.png)
   *
   * @default
   * ```json
   * "standard"
   * ```
   */
  "hillshade-method"?: PropertyValueSpecification<"standard" | "basic" | "combined" | "igor" | "multidirectional">;
  /**
   * The opacity at which the color-relief will be drawn.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "color-relief-opacity"?: PropertyValueSpecification<number>;
  "color-relief-opacity-transition"?: TransitionSpecification;
  /**
   * Defines the color of each pixel based on its elevation. Should be an expression that uses `["elevation"]` as input.
   *
   * @example
   * ```json
   * [
   *     "interpolate",
   *     ["linear"],
   *     ["elevation"],
   *     0,
   *     "black",
   *     8849,
   *     "white"
   * ]
   * ```
   */
  "color-relief-color"?: ExpressionSpecification;
  /**
   * The color with which the background will be drawn.
   *
   * @default
   * ```json
   * "#000000"
   * ```
   */
  "background-color"?: PropertyValueSpecification<ColorSpecification>;
  "background-color-transition"?: TransitionSpecification;
  /**
   * Name of image in sprite to use for drawing an image background. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
   */
  "background-pattern"?: PropertyValueSpecification<ResolvedImageSpecification>;
  "background-pattern-transition"?: TransitionSpecification;
  /**
   * The opacity at which the background will be drawn.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "background-opacity"?: PropertyValueSpecification<number>;
  "background-opacity-transition"?: TransitionSpecification;
};
/**
 * Union of all layout properties across all layer types.
 */
type AllLayoutProperties = {
  /**
   * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
   */
  "fill-sort-key"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Whether this layer is displayed.
   *
   * @default
   * ```json
   * "visible"
   * ```
   */
  "visibility"?: VisibilitySpecification;
  /**
   * The display of line endings.
   *
   * @default
   * ```json
   * "butt"
   * ```
   */
  "line-cap"?: DataDrivenPropertyValueSpecification<"butt" | "round" | "square">;
  /**
   * The display of lines when joining.
   *
   * @default
   * ```json
   * "miter"
   * ```
   */
  "line-join"?: DataDrivenPropertyValueSpecification<"bevel" | "round" | "miter">;
  /**
   * Used to automatically convert miter joins to bevel joins for sharp angles.
   *
   * @default
   * ```json
   * 2
   * ```
   */
  "line-miter-limit"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Used to automatically convert round joins to miter joins for shallow angles.
   *
   * @default
   * ```json
   * 1.05
   * ```
   */
  "line-round-limit"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
   */
  "line-sort-key"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Label placement relative to its geometry.
   *
   * @default
   * ```json
   * "point"
   * ```
   */
  "symbol-placement"?: PropertyValueSpecification<"point" | "line" | "line-center">;
  /**
   * Distance between two symbol anchors.
   *
   * @default
   * ```json
   * 250
   * ```
   */
  "symbol-spacing"?: PropertyValueSpecification<number>;
  /**
   * If true, the symbols will not cross tile edges to avoid mutual collisions. Recommended in layers that don't have enough padding in the vector tile to prevent collisions, or if it is a point symbol layer placed after a line symbol layer. When using a client that supports global collision detection, like MapLibre GL JS version 0.42.0 or greater, enabling this property is not needed to prevent clipped labels at tile boundaries.
   */
  "symbol-avoid-edges"?: PropertyValueSpecification<boolean>;
  /**
   * Sorts features in ascending order based on this value. Features with lower sort keys are drawn and placed first.  When `icon-allow-overlap` or `text-allow-overlap` is `false`, features with a lower sort key will have priority during placement. When `icon-allow-overlap` or `text-allow-overlap` is set to `true`, features with a higher sort key will overlap over features with a lower sort key.
   */
  "symbol-sort-key"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Determines whether overlapping symbols in the same layer are rendered in the order that they appear in the data source or by their y-position relative to the viewport. To control the order and prioritization of symbols otherwise, use `symbol-sort-key`.
   *
   * @default
   * ```json
   * "auto"
   * ```
   */
  "symbol-z-order"?: PropertyValueSpecification<"auto" | "viewport-y" | "source">;
  /**
   * If true, the icon will be visible even if it collides with other previously drawn symbols.
   */
  "icon-allow-overlap"?: PropertyValueSpecification<boolean>;
  /**
   * Allows for control over whether to show an icon when it overlaps other symbols on the map. If `icon-overlap` is not set, `icon-allow-overlap` is used instead.
   */
  "icon-overlap"?: PropertyValueSpecification<"never" | "always" | "cooperative">;
  /**
   * If true, other symbols can be visible even if they collide with the icon.
   */
  "icon-ignore-placement"?: PropertyValueSpecification<boolean>;
  /**
   * If true, text will display without their corresponding icons when the icon collides with other symbols and the text does not.
   */
  "icon-optional"?: PropertyValueSpecification<boolean>;
  /**
   * In combination with `symbol-placement`, determines the rotation behavior of icons.
   *
   * @default
   * ```json
   * "auto"
   * ```
   */
  "icon-rotation-alignment"?: DataDrivenPropertyValueSpecification<"map" | "viewport" | "auto">;
  /**
   * Scales the original size of the icon by the provided factor. The new pixel size of the image will be the original pixel size multiplied by `icon-size`. 1 is the original size; 3 triples the size of the image.
   *
   * @default
   * ```json
   * 1
   * ```
   */
  "icon-size"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Scales the icon to fit around the associated text.
   *
   * @default
   * ```json
   * "none"
   * ```
   */
  "icon-text-fit"?: PropertyValueSpecification<"none" | "width" | "height" | "both">;
  /**
   * Size of the additional area added to dimensions determined by `icon-text-fit`, in clockwise order: top, right, bottom, left.
   *
   * @default
   * ```json
   * [0, 0, 0, 0]
   * ```
   */
  "icon-text-fit-padding"?: PropertyValueSpecification<[number, number, number, number]>;
  /**
   * Name of image in sprite to use for drawing an image background.
   */
  "icon-image"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>;
  /**
   * Rotates the icon clockwise.
   */
  "icon-rotate"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Size of additional area round the icon bounding box used for detecting symbol collisions.
   *
   * @default
   * ```json
   * [2]
   * ```
   */
  "icon-padding"?: DataDrivenPropertyValueSpecification<PaddingSpecification>;
  /**
   * If true, the icon may be flipped to prevent it from being rendered upside-down.
   */
  "icon-keep-upright"?: PropertyValueSpecification<boolean>;
  /**
   * Offset distance of icon from its anchor. Positive values indicate right and down, while negative values indicate left and up. Each component is multiplied by the value of `icon-size` to obtain the final offset in pixels. When combined with `icon-rotate` the offset will be as if the rotated direction was up.
   *
   * @default
   * ```json
   * [0, 0]
   * ```
   */
  "icon-offset"?: DataDrivenPropertyValueSpecification<[number, number]>;
  /**
   * Part of the icon placed closest to the anchor.
   *
   * @default
   * ```json
   * "center"
   * ```
   */
  "icon-anchor"?: DataDrivenPropertyValueSpecification<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">;
  /**
   * Orientation of icon when map is pitched.
   *
   * @default
   * ```json
   * "auto"
   * ```
   */
  "icon-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport" | "auto">;
  /**
   * Orientation of text when map is pitched.
   *
   * @default
   * ```json
   * "auto"
   * ```
   */
  "text-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport" | "auto">;
  /**
   * In combination with `symbol-placement`, determines the rotation behavior of the individual glyphs forming the text.
   *
   * @default
   * ```json
   * "auto"
   * ```
   */
  "text-rotation-alignment"?: PropertyValueSpecification<"map" | "viewport" | "viewport-glyph" | "auto">;
  /**
   * Value to use for a text label. If a plain `string` is provided, it will be treated as a `formatted` with default/inherited formatting options.
   */
  "text-field"?: DataDrivenPropertyValueSpecification<FormattedSpecification>;
  /**
   * Fonts to use for displaying text. If the `glyphs` root property is specified, this array is joined together and interpreted as a font stack name. Otherwise, it is interpreted as a cascading fallback list of local font names.
   *
   * @default
   * ```json
   * ["Open Sans Regular", "Arial Unicode MS Regular"]
   * ```
   */
  "text-font"?: DataDrivenPropertyValueSpecification<Array<string>>;
  /**
   * Font size.
   *
   * @default
   * ```json
   * 16
   * ```
   */
  "text-size"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * The maximum line width for text wrapping.
   *
   * @default
   * ```json
   * 10
   * ```
   */
  "text-max-width"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Text leading value for multi-line text.
   *
   * @default
   * ```json
   * 1.2
   * ```
   */
  "text-line-height"?: PropertyValueSpecification<number>;
  /**
   * Text tracking amount.
   */
  "text-letter-spacing"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Text justification options.
   *
   * @default
   * ```json
   * "center"
   * ```
   */
  "text-justify"?: DataDrivenPropertyValueSpecification<"auto" | "left" | "center" | "right">;
  /**
   * Radial offset of text, in the direction of the symbol's anchor. Useful in combination with `text-variable-anchor`, which defaults to using the two-dimensional `text-offset` if present.
   */
  "text-radial-offset"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * To increase the chance of placing high-priority labels on the map, you can provide an array of `text-anchor` locations: the renderer will attempt to place the label at each location, in order, before moving onto the next label. Use `text-justify: auto` to choose justification based on anchor position. To apply an offset, use the `text-radial-offset` or the two-dimensional `text-offset`.
   *
   * @example
   * ```json
   * ["center", "left", "right"]
   * ```
   */
  "text-variable-anchor"?: PropertyValueSpecification<Array<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">>;
  /**
   * To increase the chance of placing high-priority labels on the map, you can provide an array of `text-anchor` locations, each paired with an offset value. The renderer will attempt to place the label at each location, in order, before moving on to the next location+offset. Use `text-justify: auto` to choose justification based on anchor position.
   *
   *  The length of the array must be even, and must alternate between enum and point entries. i.e., each anchor location must be accompanied by a point, and that point defines the offset when the corresponding anchor location is used. Positive offset values indicate right and down, while negative values indicate left and up. Anchor locations may repeat, allowing the renderer to try multiple offsets to try and place a label using the same anchor.
   *
   *  When present, this property takes precedence over `text-anchor`, `text-variable-anchor`, `text-offset`, and `text-radial-offset`.
   *
   *  ```json
   *
   *  { "text-variable-anchor-offset": ["top", [0, 4], "left", [3,0], "bottom", [1, 1]] }
   *
   *  ```
   *
   *  When the renderer chooses the `top` anchor, `[0, 4]` will be used for `text-offset`; the text will be shifted down by 4 ems.
   *
   *  When the renderer chooses the `left` anchor, `[3, 0]` will be used for `text-offset`; the text will be shifted right by 3 ems.
   *
   * @example
   * ```json
   * ["top", [0, 4], "left", [3, 0], "bottom", [1, 1]]
   * ```
   */
  "text-variable-anchor-offset"?: DataDrivenPropertyValueSpecification<VariableAnchorOffsetCollectionSpecification>;
  /**
   * Part of the text placed closest to the anchor.
   *
   * @default
   * ```json
   * "center"
   * ```
   */
  "text-anchor"?: DataDrivenPropertyValueSpecification<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">;
  /**
   * Maximum angle change between adjacent characters.
   *
   * @default
   * ```json
   * 45
   * ```
   */
  "text-max-angle"?: PropertyValueSpecification<number>;
  /**
   * The property allows control over a symbol's orientation. Note that the property values act as a hint, so that a symbol whose language doesn’t support the provided orientation will be laid out in its natural orientation. Example: English point symbol will be rendered horizontally even if array value contains single 'vertical' enum value. The order of elements in an array define priority order for the placement of an orientation variant.
   */
  "text-writing-mode"?: PropertyValueSpecification<Array<"horizontal" | "vertical">>;
  /**
   * Rotates the text clockwise.
   */
  "text-rotate"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Size of the additional area around the text bounding box used for detecting symbol collisions.
   *
   * @default
   * ```json
   * 2
   * ```
   */
  "text-padding"?: PropertyValueSpecification<number>;
  /**
   * If true, the text may be flipped vertically to prevent it from being rendered upside-down.
   *
   * @default
   * ```json
   * true
   * ```
   */
  "text-keep-upright"?: PropertyValueSpecification<boolean>;
  /**
   * Specifies how to capitalize text, similar to the CSS `text-transform` property.
   *
   * @default
   * ```json
   * "none"
   * ```
   */
  "text-transform"?: DataDrivenPropertyValueSpecification<"none" | "uppercase" | "lowercase">;
  /**
   * Offset distance of text from its anchor. Positive values indicate right and down, while negative values indicate left and up. If used with text-variable-anchor, input values will be taken as absolute values. Offsets along the x- and y-axis will be applied automatically based on the anchor position.
   *
   * @default
   * ```json
   * [0, 0]
   * ```
   */
  "text-offset"?: DataDrivenPropertyValueSpecification<[number, number]>;
  /**
   * If true, the text will be visible even if it collides with other previously drawn symbols.
   */
  "text-allow-overlap"?: PropertyValueSpecification<boolean>;
  /**
   * Allows for control over whether to show symbol text when it overlaps other symbols on the map. If `text-overlap` is not set, `text-allow-overlap` is used instead
   */
  "text-overlap"?: PropertyValueSpecification<"never" | "always" | "cooperative">;
  /**
   * If true, other symbols can be visible even if they collide with the text.
   */
  "text-ignore-placement"?: PropertyValueSpecification<boolean>;
  /**
   * If true, icons will display without their corresponding text when the text collides with other symbols and the icon does not.
   */
  "text-optional"?: PropertyValueSpecification<boolean>;
  /**
   * The height above the anchor, in meters, at which the symbol is placed. Use `symbol-height-anchor` to control what this height is measured from.
   */
  "symbol-height-offset"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * Defines what `symbol-height-offset` is measured from.
   *
   * @default
   * ```json
   * "ground"
   * ```
   */
  "symbol-height-anchor"?: PropertyValueSpecification<"ground" | "absolute">;
  /**
   * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
   */
  "circle-sort-key"?: DataDrivenPropertyValueSpecification<number>;
  /**
   * The distance from each fill extrusion corner, measured along the adjacent edges, that is replaced by a rounded corner. A value of `0` disables rounded corners.
   */
  "fill-extrusion-rounded-corner-distance"?: number;
};
//#endregion
//#region src/deref.d.ts
type LayerWithRef = LayerSpecification & {
  ref?: string;
};
/**
 *
 * The input is not modified. The output may contain references to portions
 * of the input.
 *
 * @param layers - array of layers, some of which may contain `ref` properties
 * whose value is the `id` of another property
 * @returns a new array where such layers have been augmented with the 'type', 'source', etc. properties
 * from the parent layer, and the `ref` property has been removed.
 */
export declare function derefLayers(layers: LayerWithRef[]): LayerSpecification[];
//#endregion
//#region src/diff.d.ts
/**
 * Operations that can be performed by the diff.
 * Below are the operations and their arguments, the arguments should be aligned with the style methods in maplibre-gl-js.
 */
type DiffOperationsMap = {
  setStyle: [StyleSpecification];
  addLayer: [LayerSpecification, string | undefined];
  removeLayer: [string];
  setPaintProperty: [string, keyof AllPaintProperties, AllPaintProperties[keyof AllPaintProperties]];
  setLayoutProperty: [string, keyof AllLayoutProperties, AllLayoutProperties[keyof AllLayoutProperties]];
  setFilter: [string, FilterSpecification];
  addSource: [string, SourceSpecification];
  removeSource: [string];
  setGeoJSONSourceData: [string, GeoJSONSourceSpecification['data']];
  setLayerZoomRange: [string, number, number];
  setLayerProperty: [string, string, unknown];
  setCenter: [number[]];
  setCenterAltitude: [number];
  setZoom: [number];
  setBearing: [number];
  setPitch: [number];
  setRoll: [number];
  setSprite: [SpriteSpecification];
  setGlyphs: [string];
  setFontFaces: [FontFacesSpecification];
  setTransition: [TransitionSpecification];
  setLight: [LightSpecification];
  setTerrain: [TerrainSpecification];
  setSky: [SkySpecification];
  setProjection: [ProjectionSpecification];
  setGlobalState: [StateSpecification];
};
type DiffOperations = keyof DiffOperationsMap;
/**
 * A single diff command, where the arguments are derived from the command name.
 *
 * This is distributed over `T` so that `DiffCommand<DiffOperations>` is a discriminated union
 * of all the commands, which lets a `switch` on `command` narrow `args` to a single tuple.
 */
type DiffCommand<T extends DiffOperations = DiffOperations> = T extends DiffOperations ? {
  command: T;
  args: DiffOperationsMap[T];
} : never;
/**
 * Diff two stylesheet
 *
 * Creates semanticly aware diffs that can easily be applied at runtime.
 * Operations produced by the diff closely resemble the maplibre-gl-js API. Any
 * error creating the diff will fall back to the 'setStyle' operation.
 *
 * Example diff:
 * [
 *     { command: 'setConstant', args: ['@water', '#0000FF'] },
 *     { command: 'setPaintProperty', args: ['background', 'background-color', 'black'] }
 * ]
 *
 * @private
 * @param {*} [before] stylesheet to compare from
 * @param {*} after stylesheet to compare to
 * @returns Array list of changes
 */
export declare function diff(before: StyleSpecification, after: StyleSpecification): DiffCommand<DiffOperations>[];
//#endregion
//#region src/error/validation_error.d.ts
/**
 * How badly a style is broken.
 *
 * - `error`: the style is invalid and cannot be rendered as written.
 * - `warning`: the style renders, but almost certainly not as its author intended -- for
 *   example a filter that mixes deprecated syntax into an expression tree. Consumers should
 *   surface these (a style editor lists them; a map logs them) but must keep rendering.
 */
type ValidationSeverity = 'error' | 'warning';
export declare class ValidationError {
  message: string;
  identifier: string;
  line: number;
  severity: ValidationSeverity;
  constructor(key: string, value: any & {
    __line__: number;
  }, message: string, identifier?: string | null, severity?: ValidationSeverity);
}
//#endregion
//#region src/error/parsing_error.d.ts
export declare class ParsingError {
  message: string;
  error: Error;
  line: number;
  constructor(error: Error);
}
//#endregion
//#region src/expression/parsing_error.d.ts
declare class ExpressionParsingError extends Error {
  readonly key: string;
  message: string;
  constructor(key: string, message: string);
}
//#endregion
//#region src/expression/types/color_spaces.d.ts
/**
 * @param r Red component 0..1
 * @param g Green component 0..1
 * @param b Blue component 0..1
 * @param alpha Alpha component 0..1
 */
type RGBColor = [r: number, g: number, b: number, alpha: number];
/**
 * @param h Hue as degrees 0..360
 * @param c Chroma 0..~230
 * @param l Lightness as percentage 0..100
 * @param alpha Alpha component 0..1
 */
type HCLColor = [h: number, c: number, l: number, alpha: number];
/**
 * @param l Lightness as percentage 0..100
 * @param a A axis value -125..125
 * @param b B axis value -125..125
 * @param alpha Alpha component 0..1
 */
type LABColor = [l: number, a: number, b: number, alpha: number];
//#endregion
//#region src/expression/types/color.d.ts
type InterpolationColorSpace = 'rgb' | 'hcl' | 'lab';
/**
 * Color representation used by WebGL.
 * Defined in sRGB color space and pre-blended with alpha.
 * @private
 */
export declare class Color {
  readonly r: number;
  readonly g: number;
  readonly b: number;
  readonly a: number;
  /**
   * @param r Red component premultiplied by `alpha` 0..1
   * @param g Green component premultiplied by `alpha` 0..1
   * @param b Blue component premultiplied by `alpha` 0..1
   * @param [alpha=1] Alpha component 0..1
   * @param [premultiplied=true] Whether the `r`, `g` and `b` values have already
   * been multiplied by alpha. If `true` nothing happens if `false` then they will
   * be multiplied automatically.
   */
  constructor(r: number, g: number, b: number, alpha?: number, premultiplied?: boolean);
  static black: Color;
  static white: Color;
  static transparent: Color;
  static red: Color;
  /**
   * Parses CSS color strings and converts colors to sRGB color space if needed.
   * Officially supported color formats:
   * - keyword, e.g. 'aquamarine' or 'steelblue'
   * - hex (with 3, 4, 6 or 8 digits), e.g. '#f0f' or '#e9bebea9'
   * - rgb and rgba, e.g. 'rgb(0,240,120)' or 'rgba(0%,94%,47%,0.1)' or 'rgb(0 240 120 / .3)'
   * - hsl and hsla, e.g. 'hsl(0,0%,83%)' or 'hsla(0,0%,83%,.5)' or 'hsl(0 0% 83% / 20%)'
   *
   * @param input CSS color string to parse.
   * @returns A `Color` instance, or `undefined` if the input is not a valid color string.
   */
  static parse(input: Color | string | undefined | null): Color | undefined;
  /**
   * Used in color interpolation and by 'to-rgba' expression.
   *
   * @returns Gien color, with reversed alpha blending, in sRGB color space.
   */
  get rgb(): RGBColor;
  /**
   * Used in color interpolation.
   *
   * @returns Gien color, with reversed alpha blending, in HCL color space.
   */
  get hcl(): HCLColor;
  /**
   * Used in color interpolation.
   *
   * @returns Gien color, with reversed alpha blending, in LAB color space.
   */
  get lab(): LABColor;
  /**
   * Lazy getter pattern. When getter is called for the first time lazy value
   * is calculated and then overwrites getter function in given object instance.
   *
   * @example:
   * const redColor = Color.parse('red');
   * let x = redColor.hcl; // this will invoke `get hcl()`, which will calculate
   * // the value of red in HCL space and invoke this `overwriteGetter` function
   * // which in turn will set a field with a key 'hcl' in the `redColor` object.
   * // In other words it will override `get hcl()` from its `Color` prototype
   * // with its own property: hcl = [calculated red value in hcl].
   * let y = redColor.hcl; // next call will no longer invoke getter but simply
   * // return the previously calculated value
   * x === y; // true - `x` is exactly the same object as `y`
   *
   * @param getterKey Getter key
   * @param lazyValue Lazily calculated value to be memoized by current instance
   * @private
   */
  private overwriteGetter;
  /**
   * Used by 'to-string' expression.
   *
   * @returns Serialized color in format `rgba(r,g,b,a)`
   * where r,g,b are numbers within 0..255 and alpha is number within 1..0
   *
   * @example
   * var purple = new Color.parse('purple');
   * purple.toString; // = "rgba(128,0,128,1)"
   * var translucentGreen = new Color.parse('rgba(26, 207, 26, .73)');
   * translucentGreen.toString(); // = "rgba(26,207,26,0.73)"
   */
  toString(): string;
  static interpolate(from: Color, to: Color, t: number, spaceKey?: InterpolationColorSpace): Color;
}
//#endregion
//#region src/expression/types/resolved_image.d.ts
type ResolvedImageOptions = {
  name: string;
  available: boolean;
};
export declare class ResolvedImage {
  name: string;
  available: boolean;
  constructor(options: ResolvedImageOptions);
  toString(): string;
  static fromString(name: string): ResolvedImage | null;
}
//#endregion
//#region src/expression/types/formatted.d.ts
declare const VERTICAL_ALIGN_OPTIONS: readonly ["bottom", "center", "top"];
type VerticalAlign = (typeof VERTICAL_ALIGN_OPTIONS)[number];
export declare class FormattedSection {
  text: string;
  image: ResolvedImage | null;
  scale: number | null;
  fontStack: string | null;
  textColor: Color | null;
  verticalAlign: VerticalAlign | null;
  constructor(text: string, image: ResolvedImage | null, scale: number | null, fontStack: string | null, textColor: Color | null, verticalAlign: VerticalAlign | null);
}
export declare class Formatted {
  sections: Array<FormattedSection>;
  constructor(sections: Array<FormattedSection>);
  static fromString(unformatted: string): Formatted;
  isEmpty(): boolean;
  static factory(text: Formatted | string): Formatted;
  toString(): string;
}
//#endregion
//#region src/point2d.d.ts
interface Point2D {
  x: number;
  y: number;
}
//#endregion
//#region src/tiles_and_coordinates.d.ts
interface ICanonicalTileID {
  z: number;
  x: number;
  y: number;
  key: string;
  equals(id: ICanonicalTileID): boolean;
  url(urls: Array<string>, pixelRatio: number, scheme: string | null): string;
  isChildOf(parent: ICanonicalTileID): boolean;
  getTilePoint(coord: IMercatorCoordinate): Point2D;
  toString(): string;
}
interface IMercatorCoordinate {
  x: number;
  y: number;
  z: number;
  toLngLat(): ILngLat;
  toAltitude(): number;
  meterInMercatorCoordinateUnits(): number;
}
interface ILngLat {
  lng: number;
  lat: number;
  wrap(): ILngLat;
  toArray(): [number, number];
  distanceTo(lngLat: ILngLat): number;
  toString(): string;
}
type ILngLatLike = ILngLat | {
  lng: number;
  lat: number;
} | {
  lon: number;
  lat: number;
} | [number, number];
//#endregion
//#region src/expression/evaluation_context.d.ts
export declare class EvaluationContext {
  globals: GlobalProperties;
  feature: Feature;
  featureState: FeatureState;
  formattedSection: FormattedSection;
  availableImages: Array<string>;
  canonical: ICanonicalTileID;
  _parseColorCache: Map<string, Color>;
  constructor();
  id(): any;
  geometryType(): string;
  geometry(): Point2D[][];
  canonicalID(): ICanonicalTileID;
  properties(): {
    [_: string]: any;
  };
  parseColor(input: string): Color;
}
//#endregion
//#region src/expression/types.d.ts
type NullTypeT = {
  kind: 'null';
};
type NumberTypeT = {
  kind: 'number';
};
type StringTypeT = {
  kind: 'string';
};
type BooleanTypeT = {
  kind: 'boolean';
};
type ColorTypeT = {
  kind: 'color';
};
type ProjectionDefinitionTypeT = {
  kind: 'projectionDefinition';
};
type ObjectTypeT = {
  kind: 'object';
};
type ValueTypeT = {
  kind: 'value';
};
type ErrorTypeT = {
  kind: 'error';
};
type CollatorTypeT = {
  kind: 'collator';
};
type FormattedTypeT = {
  kind: 'formatted';
};
type PaddingTypeT = {
  kind: 'padding';
};
type NumberArrayTypeT = {
  kind: 'numberArray';
};
type ColorArrayTypeT = {
  kind: 'colorArray';
};
type ResolvedImageTypeT = {
  kind: 'resolvedImage';
};
type VariableAnchorOffsetCollectionTypeT = {
  kind: 'variableAnchorOffsetCollection';
};
type EvaluationKind = 'constant' | 'source' | 'camera' | 'composite';
type Type = NullTypeT | NumberTypeT | StringTypeT | BooleanTypeT | ColorTypeT | ProjectionDefinitionTypeT | ObjectTypeT | ValueTypeT | ArrayType | ErrorTypeT | CollatorTypeT | FormattedTypeT | PaddingTypeT | NumberArrayTypeT | ColorArrayTypeT | ResolvedImageTypeT | VariableAnchorOffsetCollectionTypeT;
interface ArrayType<T extends Type = Type> {
  kind: 'array';
  itemType: T;
  N: number;
}
export declare const NullType: NullTypeT;
export declare const ColorType: ColorTypeT;
export declare const ProjectionDefinitionType: ProjectionDefinitionTypeT;
export declare const FormattedType: FormattedTypeT;
declare function typeToString(type: Type): string;
//#endregion
//#region src/expression/types/collator.d.ts
declare class Collator {
  locale: string | null;
  sensitivity: 'base' | 'accent' | 'case' | 'variant';
  collator: Intl.Collator;
  constructor(caseSensitive: boolean, diacriticSensitive: boolean, locale: string | null);
  compare(lhs: string, rhs: string): number;
  resolvedLocale(): string;
}
//#endregion
//#region src/expression/types/padding.d.ts
/**
 * A set of four numbers representing padding around a box. Create instances from
 * bare arrays or numeric values using the static method `Padding.parse`.
 * @private
 */
export declare class Padding {
  /** Padding values are in CSS order: top, right, bottom, left */
  values: [number, number, number, number];
  constructor(values: [number, number, number, number]);
  /**
   * Numeric padding values
   * @param input A padding value
   * @returns A `Padding` instance, or `undefined` if the input is not a valid padding value.
   */
  static parse(input?: number | number[] | Padding | null): Padding | undefined;
  toString(): string;
  static interpolate(from: Padding, to: Padding, t: number): Padding;
}
//#endregion
//#region src/expression/types/number_array.d.ts
/**
 * An array of numbers. Create instances from
 * bare arrays or numeric values using the static method `NumberArray.parse`.
 * @private
 */
export declare class NumberArray {
  values: number[];
  constructor(values: number[]);
  /**
   * Numeric NumberArray values
   * @param input A NumberArray value
   * @returns A `NumberArray` instance, or `undefined` if the input is not a valid NumberArray value.
   */
  static parse(input?: number | number[] | NumberArray | null): NumberArray | undefined;
  toString(): string;
  static interpolate(from: NumberArray, to: NumberArray, t: number): NumberArray;
}
//#endregion
//#region src/expression/types/color_array.d.ts
/**
 * An array of colors. Create instances from
 * bare arrays or strings using the static method `ColorArray.parse`.
 * @private
 */
export declare class ColorArray {
  values: Color[];
  constructor(values: Color[]);
  /**
   * ColorArray values
   * @param input A ColorArray value
   * @returns A `ColorArray` instance, or `undefined` if the input is not a valid ColorArray value.
   */
  static parse(input?: string | string[] | ColorArray | null): ColorArray | undefined;
  toString(): string;
  static interpolate(from: ColorArray, to: ColorArray, t: number, spaceKey?: InterpolationColorSpace): ColorArray;
}
//#endregion
//#region src/expression/types/variable_anchor_offset_collection.d.ts
/**
 * Utility class to assist managing values for text-variable-anchor-offset property. Create instances from
 * bare arrays using the static method `VariableAnchorOffsetCollection.parse`.
 * @private
 */
export declare class VariableAnchorOffsetCollection {
  /** Series of paired of anchor (string) and offset (point) values */
  values: VariableAnchorOffsetCollectionSpecification;
  constructor(values: VariableAnchorOffsetCollectionSpecification);
  static parse(input?: VariableAnchorOffsetCollectionSpecification | VariableAnchorOffsetCollection): VariableAnchorOffsetCollection | undefined;
  toString(): string;
  static interpolate(from: VariableAnchorOffsetCollection, to: VariableAnchorOffsetCollection, t: number, key: string): VariableAnchorOffsetCollection;
}
//#endregion
//#region src/expression/types/projection_definition.d.ts
export declare class ProjectionDefinition {
  readonly from: string;
  readonly to: string;
  readonly transition: number;
  constructor(from: string, to: string, transition: number);
  toString(): string;
  static interpolate(from: string, to: string, t: number): ProjectionDefinition;
  static parse(input?: any): ProjectionDefinition;
}
//#endregion
//#region src/expression/values.d.ts
type Value = null | string | boolean | number | Color | ProjectionDefinition | Collator | Formatted | Padding | NumberArray | ColorArray | ResolvedImage | VariableAnchorOffsetCollection | ReadonlyArray<Value> | {
  readonly [x: string]: Value;
};
export declare function typeOf(value: Value): Type;
//#endregion
//#region src/expression/scope.d.ts
/**
 * Tracks `let` bindings during expression parsing.
 * @private
 */
declare class Scope {
  parent: Scope;
  bindings: {
    [_: string]: Expression;
  };
  constructor(parent?: Scope, bindings?: Array<[string, Expression]>);
  concat(bindings: Array<[string, Expression]>): Scope;
  get(name: string): Expression;
  has(name: string): boolean;
}
//#endregion
//#region src/expression/parsing_context.d.ts
/**
 * State associated parsing at a given point in an expression tree.
 * @private
 */
declare class ParsingContext {
  registry: ExpressionRegistry;
  path: Array<number>;
  readonly key: string;
  scope: Scope;
  errors: Array<ExpressionParsingError>;
  expectedType: Type;
  /**
   * Internal delegate to inConstant function to avoid circular dependency to CompoundExpression
   */
  private _isConstant;
  constructor(registry: ExpressionRegistry, isConstantFunc: (expression: Expression) => boolean, path?: Array<number>, expectedType?: Type | null, scope?: Scope, errors?: Array<ExpressionParsingError>);
  /**
   * @param expr the JSON expression to parse
   * @param index the optional argument index if this expression is an argument of a parent expression that's being parsed
   * @param options
   * @param options.omitTypeAnnotations set true to omit inferred type annotations.  Caller beware: with this option set, the parsed expression's type will NOT satisfy `expectedType` if it would normally be wrapped in an inferred annotation.
   * @private
   */
  parse(expr: unknown, index?: number, expectedType?: Type | null, bindings?: Array<[string, Expression]>, options?: {
    typeAnnotation?: 'assert' | 'coerce' | 'omit';
  }): Expression;
  _parse(expr: unknown, options: {
    typeAnnotation?: 'assert' | 'coerce' | 'omit';
  }): Expression;
  /**
   * Returns a copy of this context suitable for parsing the subexpression at
   * index `index`, optionally appending to 'let' binding map.
   *
   * Note that `errors` property, intended for collecting errors while
   * parsing, is copied by reference rather than cloned.
   * @private
   */
  concat(index: number, expectedType?: Type | null, bindings?: Array<[string, Expression]>): ParsingContext;
  /**
   * Push a parsing (or type checking) error into the `this.errors`
   * @param error The message
   * @param keys Optionally specify the source of the error at a child
   * of the current expression at `this.key`.
   * @private
   */
  error(error: string, ...keys: Array<number>): void;
  /**
   * Returns null if `t` is a subtype of `expected`; otherwise returns an
   * error message and also pushes it to `this.errors`.
   * @param expected The expected type
   * @param t The actual type
   * @returns null if `t` is a subtype of `expected`; otherwise returns an error message
   */
  checkSubtype(expected: Type, t: Type): string;
}
//#endregion
//#region src/expression/expression.d.ts
/**
 * Expression
 */
interface Expression {
  readonly type: Type;
  evaluate(ctx: EvaluationContext): any;
  eachChild(fn: (a: Expression) => void): void;
  /**
   * Statically analyze the expression, attempting to enumerate possible outputs. Returns
   * false if the complete set of outputs is statically undecidable, otherwise true.
   */
  outputDefined(): boolean;
}
type ExpressionParser = (args: ReadonlyArray<unknown>, context: ParsingContext) => Expression;
type ExpressionRegistration = {
  new (...args: any): Expression;
} & {
  readonly parse: ExpressionParser;
};
type ExpressionRegistry = {
  [_: string]: ExpressionRegistration;
};
//#endregion
//#region src/util/result.d.ts
/**
 * A type used for returning and propagating errors. The first element of the union
 * represents success and contains a value, and the second represents an error and
 * contains an error value.
 * @private
 */
type Result<T, E> = {
  result: 'success';
  value: T;
} | {
  result: 'error';
  value: E;
};
//#endregion
//#region src/util/interpolate-primitives.d.ts
declare function interpolateNumber(from: number, to: number, t: number): number;
declare function interpolateArray<T extends number[]>(from: T, to: T, t: number): T;
//#endregion
//#region src/expression/stops.d.ts
type Stops = Array<[number, Expression]>;
//#endregion
//#region src/expression/definitions/interpolate.d.ts
type InterpolationType = {
  name: 'linear';
} | {
  name: 'exponential';
  base: number;
} | {
  name: 'cubic-bezier';
  controlPoints: [number, number, number, number];
};
type InterpolatedValueType = NumberTypeT | ColorTypeT | ProjectionDefinitionTypeT | PaddingTypeT | NumberArrayTypeT | ColorArrayTypeT | VariableAnchorOffsetCollectionTypeT | ArrayType<NumberTypeT>;
export declare class Interpolate implements Expression {
  type: InterpolatedValueType;
  operator: 'interpolate' | 'interpolate-hcl' | 'interpolate-lab';
  interpolation: InterpolationType;
  input: Expression;
  readonly key: string;
  labels: Array<number>;
  outputs: Array<Expression>;
  constructor(type: InterpolatedValueType, operator: 'interpolate' | 'interpolate-hcl' | 'interpolate-lab', interpolation: InterpolationType, input: Expression, stops: Stops, key: string);
  static interpolationFactor(interpolation: InterpolationType, input: number, lower: number, upper: number): number;
  static parse(args: ReadonlyArray<unknown>, context: ParsingContext): Expression;
  evaluate(ctx: EvaluationContext): any;
  eachChild(fn: (_: Expression) => void): void;
  outputDefined(): boolean;
}
declare const interpolateFactory: {
  color: typeof Color.interpolate;
  number: typeof interpolateNumber;
  padding: typeof Padding.interpolate;
  numberArray: typeof NumberArray.interpolate;
  colorArray: typeof ColorArray.interpolate;
  variableAnchorOffsetCollection: typeof VariableAnchorOffsetCollection.interpolate;
  array: typeof interpolateArray;
};
//#endregion
//#region src/function/index.d.ts
type StyleFunction = {
  kind: 'source' | 'camera' | 'composite';
  interpolationType?: InterpolationType | null;
  interpolationFactor?: (input: number, lower: number, upper: number) => number;
  zoomStops?: Array<number>;
  evaluate: (globals: GlobalProperties, feature?: Partial<Feature>) => any;
};
export declare function isFunction(value: any): boolean;
export declare function createFunction(parameters: any, propertySpec: any): StyleFunction;
//#endregion
//#region src/expression/index.d.ts
type Feature = {
  readonly type: 0 | 1 | 2 | 3 | 'Unknown' | 'Point' | 'MultiPoint' | 'LineString' | 'MultiLineString' | 'Polygon' | 'MultiPolygon';
  readonly id?: any;
  readonly properties: {
    [_: string]: any;
  };
  readonly patterns?: {
    [_: string]: {
      min: string;
      mid: string;
      max: string;
    };
  };
  readonly dashes?: {
    [_: string]: {
      min: string;
      mid: string;
      max: string;
    };
  };
  readonly geometry?: Array<Array<Point2D>>;
};
type FeatureState = {
  [_: string]: any;
};
type GlobalProperties = Readonly<{
  zoom: number;
  heatmapDensity?: number;
  elevation?: number;
  lineProgress?: number;
  isSupportedScript?: (_: string) => boolean;
  accumulated?: Value;
  globalState?: Record<string, any>;
}>;
export declare class StyleExpression {
  expression: Expression;
  _evaluator: EvaluationContext;
  _defaultValue: Value;
  _warningHistory: {
    [key: string]: boolean;
  };
  _enumValues: {
    [_: string]: any;
  };
  readonly _globalState: Record<string, any>;
  readonly _rootKey: string;
  constructor(expression: Expression, rootKey: string, propertySpec?: StylePropertySpecification | null, globalState?: Record<string, any>);
  evaluateWithoutErrorHandling(globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>, formattedSection?: FormattedSection): any;
  evaluate(globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>, formattedSection?: FormattedSection): any;
}
export declare function isExpression(expression: unknown): boolean;
/**
 * Parse and typecheck the given style spec JSON expression.  If
 * options.defaultValue is provided, then the resulting StyleExpression's
 * `evaluate()` method will handle errors by logging a warning (once per
 * message) and returning the default value.  Otherwise, it will throw
 * evaluation errors.
 *
 * @private
 */
export declare function createExpression(expression: unknown, rootKey: string, propertySpec?: StylePropertySpecification | null, globalState?: Record<string, any>): Result<StyleExpression, Array<ExpressionParsingError>>;
export declare class ZoomConstantExpression<Kind extends EvaluationKind> {
  kind: Kind;
  isStateDependent: boolean;
  globalStateRefs: Set<string>;
  _styleExpression: StyleExpression;
  readonly _globalState: Record<string, any>;
  constructor(kind: Kind, expression: StyleExpression, globalState?: Record<string, any>);
  evaluateWithoutErrorHandling(globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>, formattedSection?: FormattedSection): any;
  evaluate(globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>, formattedSection?: FormattedSection): any;
}
export declare class ZoomDependentExpression<Kind extends EvaluationKind> {
  kind: Kind;
  zoomStops: Array<number>;
  isStateDependent: boolean;
  globalStateRefs: Set<string>;
  _styleExpression: StyleExpression;
  interpolationType: InterpolationType;
  readonly _globalState: Record<string, any>;
  constructor(kind: Kind, expression: StyleExpression, zoomStops: Array<number>, interpolationType?: InterpolationType, globalState?: Record<string, any>);
  evaluateWithoutErrorHandling(globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>, formattedSection?: FormattedSection): any;
  evaluate(globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>, formattedSection?: FormattedSection): any;
  interpolationFactor(input: number, lower: number, upper: number): number;
}
export declare function isZoomExpression(expression: any): expression is ZoomConstantExpression<'source'> | ZoomDependentExpression<'source'>;
type ConstantExpression = {
  kind: 'constant';
  globalStateRefs: Set<string>;
  readonly _globalState: Record<string, any>;
  readonly evaluate: (globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>) => any;
};
type SourceExpression = {
  kind: 'source';
  isStateDependent: boolean;
  globalStateRefs: Set<string>;
  readonly _globalState: Record<string, any>;
  readonly evaluate: (globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>, formattedSection?: FormattedSection) => any;
};
type CameraExpression = {
  kind: 'camera';
  globalStateRefs: Set<string>;
  readonly _globalState: Record<string, any>;
  readonly evaluate: (globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>) => any;
  readonly interpolationFactor: (input: number, lower: number, upper: number) => number;
  zoomStops: Array<number>;
  interpolationType: InterpolationType;
};
type CompositeExpression = {
  kind: 'composite';
  isStateDependent: boolean;
  globalStateRefs: Set<string>;
  readonly _globalState: Record<string, any>;
  readonly evaluate: (globals: GlobalProperties, feature?: Feature, featureState?: FeatureState, canonical?: ICanonicalTileID, availableImages?: Array<string>, formattedSection?: FormattedSection) => any;
  readonly interpolationFactor: (input: number, lower: number, upper: number) => number;
  zoomStops: Array<number>;
  interpolationType: InterpolationType;
};
type StylePropertyExpression = ConstantExpression | SourceExpression | CameraExpression | CompositeExpression;
export declare function createPropertyExpression(expressionInput: unknown, rootKey: string, propertySpec: StylePropertySpecification, globalState?: Record<string, any>): Result<StylePropertyExpression, Array<ExpressionParsingError>>;
export declare class StylePropertyFunction<T> {
  _parameters: PropertyValueSpecification<T>;
  _specification: StylePropertySpecification;
  readonly _rootKey: string;
  readonly _defaultValue: Value;
  _warningHistory: {
    [key: string]: boolean;
  };
  _innerEvaluate: (globals: GlobalProperties, feature?: Feature) => any;
  kind: StyleFunction['kind'];
  interpolationFactor: (input: number, lower: number, upper: number) => number;
  zoomStops: Array<number>;
  interpolationType: InterpolationType | null;
  isStateDependent: boolean;
  globalStateRefs: Set<string>;
  readonly _globalState: Record<string, any>;
  constructor(parameters: PropertyValueSpecification<T>, rootKey: string, specification: StylePropertySpecification);
  /**
   * Evaluates the legacy function, handling a runtime throw (e.g. interpolating
   * mismatched value types) by warning with the property location and falling
   * back to the spec default, mirroring {@link StyleExpression.evaluate}.
   * @param globals Global evaluation properties (e.g. zoom)
   * @param feature The feature being evaluated, if any
   * @returns The function result, or the spec default if evaluation throws
   */
  evaluate(globals: GlobalProperties, feature?: Feature): any;
  static deserialize<T>(serialized: {
    _parameters: PropertyValueSpecification<T>;
    _specification: StylePropertySpecification;
    _rootKey: string;
  }): StylePropertyFunction<T>;
  static serialize<T>(input: StylePropertyFunction<T>): {
    _parameters: PropertyValueSpecification<T>;
    _specification: StylePropertySpecification;
    _rootKey: string;
  };
}
export declare function normalizePropertyExpression<T>(value: PropertyValueSpecification<T>, rootKey: string, specification: StylePropertySpecification, globalState?: Record<string, any>): StylePropertyExpression;
//#endregion
//#region src/feature_filter/index.d.ts
type FilterExpression = (globalProperties: GlobalProperties, feature: Feature, canonical?: ICanonicalTileID) => boolean;
type FeatureFilter = {
  filter: FilterExpression;
  needGeometry: boolean;
  getGlobalStateRefs: () => Set<string>;
};
declare function isExpressionFilter(filter: any): filter is ExpressionFilterSpecification;
/**
 * Given a filter expressed as nested arrays, return a new function
 * that evaluates whether a given feature (with a .properties or .tags property)
 * passes its test.
 *
 * @private
 * @param filter MapLibre filter
 * @param rootKey Location of the filter in the style JSON (e.g. `layers[3].filter`),
 * used to prefix runtime warnings
 * @param [globalState] Global state object to be used for evaluating 'global-state' expressions
 * @returns filter-evaluating function
 */
export declare function featureFilter(filter: FilterSpecification | void, rootKey: string, globalState?: Record<string, any>): FeatureFilter;
//#endregion
//#region src/feature_filter/convert.d.ts
type ExpectedTypes = {
  [_: string]: ExpressionInputType;
};
export declare function convertFilter(filter: FilterSpecification, expectedTypes?: ExpectedTypes): ExpressionFilterSpecification;
//#endregion
//#region src/function/convert.d.ts
export declare function convertFunction(parameters: any, propertySpec: StylePropertySpecification): any;
//#endregion
//#region src/visit.d.ts
declare function eachSource(style: StyleSpecification, callback: (_: SourceSpecification) => void): void;
declare function eachLayer(style: StyleSpecification, callback: (_: LayerSpecification) => void): void;
type PropertyCallback = (a: {
  path: [string, 'paint' | 'layout', string];
  key: string;
  value: PropertyValueSpecification<unknown> | DataDrivenPropertyValueSpecification<unknown>;
  reference: StylePropertySpecification | null;
  set: (a: PropertyValueSpecification<unknown> | DataDrivenPropertyValueSpecification<unknown>) => void;
}) => void;
declare function eachProperty(style: StyleSpecification, options: {
  paint?: boolean;
  layout?: boolean;
}, callback: PropertyCallback): void;
//#endregion
//#region src/util/properties.d.ts
export declare function supportsPropertyExpression(spec: StylePropertySpecification): boolean;
//#endregion
//#region src/expression/definitions/index.d.ts
export declare const expressions: ExpressionRegistry;
//#endregion
//#region src/group_by_layout.d.ts
/**
 * Groups layers by their layout-affecting properties.
 * These are the properties that were formerly used by explicit `ref` mechanism
 * for layers: 'type', 'source', 'source-layer', 'minzoom', 'maxzoom',
 * 'filter', and 'layout'.
 *
 * The input is not modified. The output layers are references to the
 * input layers.
 *
 * @param layers - an array of {@link LayerSpecification}.
 * @param cachedKeys - an object to keep already calculated keys.
 * @returns an array of arrays of {@link LayerSpecification} objects, where each inner array
 * contains layers that share the same layout-affecting properties.
 */
export declare function groupByLayout(layers: LayerSpecification[], cachedKeys?: Record<string, string>): LayerSpecification[][];
//#endregion
//#region src/empty.d.ts
export declare function emptyStyle(): StyleSpecification;
//#endregion
//#region src/validate_style.min.d.ts
/**
 * Validate a MapLibre style against the style specification.
 * Use this when running in the browser.
 *
 * @param style - The style to be validated.
 * @param styleSpec - The style specification to validate against.
 * If omitted, the latest style spec is used.
 * @returns an array of errors, or an empty array if no errors are found.
 * @example
 *   const validate = require('@maplibre/maplibre-gl-style-spec/').validateStyleMin;
 *   const errors = validate(style);
 */
export declare function validateStyleMin(style: StyleSpecification, styleSpec?: {
  $version: number;
  $root: {
    version: {
      required: boolean;
      type: string;
      values: number[];
      doc: string;
      example: number;
    };
    name: {
      type: string;
      doc: string;
      example: string;
    };
    metadata: {
      type: string;
      doc: string;
      example: {
        "styleeditor:slimmode": boolean;
        "styleeditor:comment": string;
        "styleeditor:version": string;
        "example:object": {
          String: string;
          Number: number;
          Boolean: boolean;
        };
      };
    };
    center: {
      type: string;
      value: string;
      length: number;
      doc: string;
      example: number[];
    };
    centerAltitude: {
      type: string;
      doc: string;
      example: number;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    zoom: {
      type: string;
      doc: string;
      example: number;
    };
    bearing: {
      type: string;
      default: number;
      period: number;
      units: string;
      doc: string;
      example: number;
    };
    pitch: {
      type: string;
      default: number;
      units: string;
      doc: string;
      example: number;
      "sdk-support": {
        "0-60 degrees": {
          js: string;
          android: string;
          ios: string;
        };
        "0-85 degrees": {
          js: string;
          android: string;
          ios: string;
        };
        "0-180 degrees": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    roll: {
      type: string;
      default: number;
      units: string;
      doc: string;
      example: number;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    state: {
      type: string;
      default: {};
      doc: string;
      example: {
        chargerType: {
          default: string[];
        };
        minPreferredChargingSpeed: {
          default: number;
        };
      };
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    light: {
      type: string;
      doc: string;
      example: {
        anchor: string;
        color: string;
        intensity: number;
      };
    };
    sky: {
      type: string;
      doc: string;
      example: {
        "sky-color": string;
        "sky-horizon-blend": number;
        "horizon-color": string;
        "horizon-fog-blend": number;
        "fog-color": string;
        "fog-ground-blend": number;
        "atmosphere-blend": (string | number | string[])[];
      };
    };
    projection: {
      type: string;
      doc: string;
      example: {
        type: (string | number | string[])[];
      };
    };
    terrain: {
      type: string;
      doc: string;
      example: {
        source: string;
        exaggeration: number;
      };
    };
    sources: {
      required: boolean;
      type: string;
      doc: string;
      example: {
        "maplibre-demotiles": {
          type: string;
          url: string;
        };
        "maplibre-tilejson": {
          type: string;
          url: string;
        };
        "maplibre-streets": {
          type: string;
          tiles: string[];
          maxzoom: number;
        };
        "wms-imagery": {
          type: string;
          tiles: string[];
          tileSize: number;
        };
      };
    };
    sprite: {
      type: string;
      doc: string;
      example: string;
    };
    glyphs: {
      type: string;
      doc: string;
      example: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "omit to use local fonts": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "font-faces": {
      type: string;
      doc: string;
      example: {
        "Noto Sans Regular": {
          url: string;
          "unicode-range": string[];
        }[];
        Unifont: string;
      };
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    transition: {
      type: string;
      doc: string;
      example: {
        duration: number;
        delay: number;
      };
    };
    layers: {
      required: boolean;
      type: string;
      value: string;
      doc: string;
      example: {
        id: string;
        source: string;
        "source-layer": string;
        type: string;
        paint: {
          "line-color": string;
        };
      }[];
    };
  };
  sources: {
    "*": {
      type: string;
      doc: string;
    };
  };
  source: string[];
  source_vector: {
    type: {
      required: boolean;
      type: string;
      values: {
        vector: {
          doc: string;
        };
      };
      doc: string;
    };
    url: {
      type: string;
      doc: string;
    };
    tiles: {
      type: string;
      value: string;
      doc: string;
    };
    bounds: {
      type: string;
      value: string;
      length: number;
      default: number[];
      doc: string;
    };
    scheme: {
      type: string;
      values: {
        xyz: {
          doc: string;
        };
        tms: {
          doc: string;
        };
      };
      default: string;
      doc: string;
    };
    minzoom: {
      type: string;
      default: number;
      doc: string;
    };
    maxzoom: {
      type: string;
      default: number;
      doc: string;
    };
    attribution: {
      type: string;
      doc: string;
    };
    promoteId: {
      type: string;
      doc: string;
    };
    volatile: {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          android: string;
          ios: string;
          js: string;
        };
      };
    };
    encoding: {
      type: string;
      values: {
        mvt: {
          doc: string;
        };
        mlt: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        mvt: {
          android: string;
          ios: string;
          js: string;
        };
        mlt: {
          android: string;
          ios: string;
          js: string;
        };
      };
    };
    "*": {
      type: string;
      doc: string;
    };
  };
  source_raster: {
    type: {
      required: boolean;
      type: string;
      values: {
        raster: {
          doc: string;
        };
      };
      doc: string;
    };
    url: {
      type: string;
      doc: string;
    };
    tiles: {
      type: string;
      value: string;
      doc: string;
    };
    bounds: {
      type: string;
      value: string;
      length: number;
      default: number[];
      doc: string;
    };
    minzoom: {
      type: string;
      default: number;
      doc: string;
    };
    maxzoom: {
      type: string;
      default: number;
      doc: string;
    };
    tileSize: {
      type: string;
      default: number;
      units: string;
      doc: string;
    };
    scheme: {
      type: string;
      values: {
        xyz: {
          doc: string;
        };
        tms: {
          doc: string;
        };
      };
      default: string;
      doc: string;
    };
    attribution: {
      type: string;
      doc: string;
    };
    volatile: {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          android: string;
          ios: string;
          js: string;
        };
      };
    };
    "*": {
      type: string;
      doc: string;
    };
  };
  source_raster_dem: {
    type: {
      required: boolean;
      type: string;
      values: {
        "raster-dem": {
          doc: string;
        };
      };
      doc: string;
    };
    url: {
      type: string;
      doc: string;
    };
    tiles: {
      type: string;
      value: string;
      doc: string;
    };
    bounds: {
      type: string;
      value: string;
      length: number;
      default: number[];
      doc: string;
    };
    minzoom: {
      type: string;
      default: number;
      doc: string;
    };
    maxzoom: {
      type: string;
      default: number;
      doc: string;
    };
    tileSize: {
      type: string;
      default: number;
      units: string;
      doc: string;
    };
    attribution: {
      type: string;
      doc: string;
    };
    encoding: {
      type: string;
      values: {
        terrarium: {
          doc: string;
        };
        mapbox: {
          doc: string;
        };
        custom: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "mapbox, terrarium": {
          js: string;
          ios: string;
          android: string;
        };
        custom: {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    redFactor: {
      type: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    blueFactor: {
      type: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    greenFactor: {
      type: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    baseShift: {
      type: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    volatile: {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          android: string;
          ios: string;
          js: string;
        };
      };
    };
    "*": {
      type: string;
      doc: string;
    };
  };
  source_geojson: {
    type: {
      required: boolean;
      type: string;
      values: {
        geojson: {
          doc: string;
        };
      };
      doc: string;
    };
    data: {
      required: boolean;
      type: string;
      doc: string;
    };
    maxzoom: {
      type: string;
      default: number;
      doc: string;
    };
    attribution: {
      type: string;
      doc: string;
    };
    buffer: {
      type: string;
      default: number;
      maximum: number;
      minimum: number;
      doc: string;
    };
    filter: {
      type: string;
      doc: string;
    };
    tolerance: {
      type: string;
      default: number;
      doc: string;
    };
    cluster: {
      type: string;
      default: boolean;
      doc: string;
    };
    clusterRadius: {
      type: string;
      default: number;
      minimum: number;
      doc: string;
    };
    clusterMaxZoom: {
      type: string;
      doc: string;
    };
    clusterMinPoints: {
      type: string;
      doc: string;
    };
    clusterProperties: {
      type: string;
      doc: string;
    };
    lineMetrics: {
      type: string;
      default: boolean;
      doc: string;
    };
    generateId: {
      type: string;
      default: boolean;
      doc: string;
    };
    promoteId: {
      type: string;
      doc: string;
    };
  };
  source_video: {
    type: {
      required: boolean;
      type: string;
      values: {
        video: {
          doc: string;
        };
      };
      doc: string;
    };
    urls: {
      required: boolean;
      type: string;
      value: string;
      doc: string;
    };
    coordinates: {
      required: boolean;
      doc: string;
      type: string;
      length: number;
      value: {
        type: string;
        length: number;
        value: string;
        doc: string;
      };
    };
  };
  source_image: {
    type: {
      required: boolean;
      type: string;
      values: {
        image: {
          doc: string;
        };
      };
      doc: string;
    };
    url: {
      type: string;
      doc: string;
    };
    coordinates: {
      required: boolean;
      doc: string;
      type: string;
      length: number;
      value: {
        type: string;
        length: number;
        value: string;
        doc: string;
      };
    };
  };
  layer: {
    id: {
      type: string;
      doc: string;
      required: boolean;
    };
    type: {
      type: string;
      values: {
        fill: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        line: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        symbol: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        circle: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        heatmap: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        "fill-extrusion": {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        raster: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        hillshade: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
            "additional methods": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        "color-relief": {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
        background: {
          doc: string;
          "sdk-support": {
            "basic functionality": {
              js: string;
              android: string;
              ios: string;
            };
          };
        };
      };
      doc: string;
      required: boolean;
    };
    metadata: {
      type: string;
      doc: string;
      example: {
        "source:comment": string;
      };
    };
    source: {
      type: string;
      doc: string;
    };
    "source-layer": {
      type: string;
      doc: string;
    };
    minzoom: {
      type: string;
      minimum: number;
      maximum: number;
      doc: string;
    };
    maxzoom: {
      type: string;
      minimum: number;
      maximum: number;
      doc: string;
    };
    filter: {
      type: string;
      doc: string;
    };
    layout: {
      type: string;
      doc: string;
    };
    paint: {
      type: string;
      doc: string;
    };
  };
  layout: string[];
  layout_background: {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_fill: {
    "fill-sort-key": {
      type: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_circle: {
    "circle-sort-key": {
      type: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_heatmap: {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  "layout_fill-extrusion": {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-rounded-corner-distance": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
      "property-type": string;
    };
  };
  layout_line: {
    "line-cap": {
      type: string;
      values: {
        butt: {
          doc: string;
        };
        round: {
          doc: string;
        };
        square: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-join": {
      type: string;
      values: {
        bevel: {
          doc: string;
        };
        round: {
          doc: string;
        };
        miter: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-miter-limit": {
      type: string;
      default: number;
      doc: string;
      requires: {
        "line-join": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-round-limit": {
      type: string;
      default: number;
      doc: string;
      requires: {
        "line-join": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-sort-key": {
      type: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_symbol: {
    "symbol-placement": {
      type: string;
      values: {
        point: {
          doc: string;
        };
        line: {
          doc: string;
        };
        "line-center": {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "`line-center` value": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-spacing": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: {
        "symbol-placement": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-avoid-edges": {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-sort-key": {
      type: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-z-order": {
      type: string;
      values: {
        auto: {
          doc: string;
        };
        "viewport-y": {
          doc: string;
        };
        source: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-allow-overlap": {
      type: string;
      default: boolean;
      doc: string;
      requires: (string | {
        "!": string;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-overlap": {
      type: string;
      values: {
        never: {
          doc: string;
        };
        always: {
          doc: string;
        };
        cooperative: {
          doc: string;
        };
      };
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-ignore-placement": {
      type: string;
      default: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-optional": {
      type: string;
      default: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-rotation-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
        auto: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "`auto` value": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-size": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-text-fit": {
      type: string;
      values: {
        none: {
          doc: string;
        };
        width: {
          doc: string;
        };
        height: {
          doc: string;
        };
        both: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "stretchable icons": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-text-fit-padding": {
      type: string;
      value: string;
      length: number;
      default: number[];
      units: string;
      doc: string;
      requires: (string | {
        "icon-text-fit": string[];
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-image": {
      type: string;
      doc: string;
      tokens: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-rotate": {
      type: string;
      default: number;
      period: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-padding": {
      type: string;
      default: number[];
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-keep-upright": {
      type: string;
      default: boolean;
      doc: string;
      requires: (string | {
        "icon-rotation-alignment": string;
        "symbol-placement"?: undefined;
      } | {
        "symbol-placement": string[];
        "icon-rotation-alignment"?: undefined;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-offset": {
      type: string;
      value: string;
      length: number;
      default: number[];
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-anchor": {
      type: string;
      values: {
        center: {
          doc: string;
        };
        left: {
          doc: string;
        };
        right: {
          doc: string;
        };
        top: {
          doc: string;
        };
        bottom: {
          doc: string;
        };
        "top-left": {
          doc: string;
        };
        "top-right": {
          doc: string;
        };
        "bottom-left": {
          doc: string;
        };
        "bottom-right": {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-pitch-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
        auto: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-pitch-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
        auto: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "`auto` value": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-rotation-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
        "viewport-glyph": {
          doc: string;
        };
        auto: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "`auto` value": {
          js: string;
          android: string;
          ios: string;
        };
        "`viewport-glyph` value": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-field": {
      type: string;
      default: string;
      tokens: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-font": {
      type: string;
      value: string;
      default: string[];
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "local fonts": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-size": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-max-width": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-line-height": {
      type: string;
      default: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-letter-spacing": {
      type: string;
      default: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-justify": {
      type: string;
      values: {
        auto: {
          doc: string;
        };
        left: {
          doc: string;
        };
        center: {
          doc: string;
        };
        right: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        auto: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-radial-offset": {
      type: string;
      units: string;
      default: number;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      requires: string[];
      "property-type": string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
    };
    "text-variable-anchor": {
      type: string;
      value: string;
      values: {
        center: {
          doc: string;
        };
        left: {
          doc: string;
        };
        right: {
          doc: string;
        };
        top: {
          doc: string;
        };
        bottom: {
          doc: string;
        };
        "top-left": {
          doc: string;
        };
        "top-right": {
          doc: string;
        };
        "bottom-left": {
          doc: string;
        };
        "bottom-right": {
          doc: string;
        };
      };
      requires: (string | {
        "symbol-placement": string[];
      })[];
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      example: string[];
      "property-type": string;
    };
    "text-variable-anchor-offset": {
      type: string;
      requires: (string | {
        "symbol-placement": string[];
      })[];
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
        "data-driven styling": {
          js: string;
          ios: string;
          android: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      example: (string | number[])[];
      "property-type": string;
    };
    "text-anchor": {
      type: string;
      values: {
        center: {
          doc: string;
        };
        left: {
          doc: string;
        };
        right: {
          doc: string;
        };
        top: {
          doc: string;
        };
        bottom: {
          doc: string;
        };
        "top-left": {
          doc: string;
        };
        "top-right": {
          doc: string;
        };
        "bottom-left": {
          doc: string;
        };
        "bottom-right": {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: (string | {
        "!": string;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-max-angle": {
      type: string;
      default: number;
      units: string;
      doc: string;
      requires: (string | {
        "symbol-placement": string[];
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-writing-mode": {
      type: string;
      value: string;
      values: {
        horizontal: {
          doc: string;
        };
        vertical: {
          doc: string;
        };
      };
      doc: string;
      requires: (string | {
        "symbol-placement": string[];
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-rotate": {
      type: string;
      default: number;
      period: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-padding": {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-keep-upright": {
      type: string;
      default: boolean;
      doc: string;
      requires: (string | {
        "text-rotation-alignment": string;
        "symbol-placement"?: undefined;
      } | {
        "symbol-placement": string[];
        "text-rotation-alignment"?: undefined;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-transform": {
      type: string;
      values: {
        none: {
          doc: string;
        };
        uppercase: {
          doc: string;
        };
        lowercase: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-offset": {
      type: string;
      doc: string;
      value: string;
      units: string;
      length: number;
      default: number[];
      requires: (string | {
        "!": string;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-allow-overlap": {
      type: string;
      default: boolean;
      doc: string;
      requires: (string | {
        "!": string;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-overlap": {
      type: string;
      values: {
        never: {
          doc: string;
        };
        always: {
          doc: string;
        };
        cooperative: {
          doc: string;
        };
      };
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-ignore-placement": {
      type: string;
      default: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-optional": {
      type: string;
      default: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-height-offset": {
      type: string;
      default: number;
      units: string;
      doc: string;
      requires: {
        "symbol-placement": string[];
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "symbol-height-anchor": {
      type: string;
      values: {
        ground: {
          doc: string;
        };
        absolute: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_raster: {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  layout_hillshade: {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  "layout_color-relief": {
    visibility: {
      type: string;
      values: {
        visible: {
          doc: string;
        };
        none: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  filter: {
    type: string;
    doc: string;
    expression: {
      interpolated: boolean;
      parameters: string[];
    };
    "property-type": string;
  };
  filter_operator: {
    type: string;
    values: {
      "==": {
        doc: string;
      };
      "!=": {
        doc: string;
      };
      ">": {
        doc: string;
      };
      ">=": {
        doc: string;
      };
      "<": {
        doc: string;
      };
      "<=": {
        doc: string;
      };
      in: {
        doc: string;
      };
      "!in": {
        doc: string;
      };
      all: {
        doc: string;
      };
      any: {
        doc: string;
      };
      none: {
        doc: string;
      };
      has: {
        doc: string;
      };
      "!has": {
        doc: string;
      };
    };
    doc: string;
  };
  geometry_type: {
    type: string;
    values: {
      Point: {
        doc: string;
      };
      LineString: {
        doc: string;
      };
      Polygon: {
        doc: string;
      };
    };
    doc: string;
  };
  function: {
    expression: {
      type: string;
      doc: string;
    };
    stops: {
      type: string;
      doc: string;
      value: string;
    };
    base: {
      type: string;
      default: number;
      minimum: number;
      doc: string;
    };
    property: {
      type: string;
      doc: string;
      default: string;
    };
    type: {
      type: string;
      values: {
        identity: {
          doc: string;
        };
        exponential: {
          doc: string;
        };
        interval: {
          doc: string;
        };
        categorical: {
          doc: string;
        };
      };
      doc: string;
      default: string;
    };
    colorSpace: {
      type: string;
      values: {
        rgb: {
          doc: string;
        };
        lab: {
          doc: string;
        };
        hcl: {
          doc: string;
        };
      };
      doc: string;
      default: string;
    };
    default: {
      type: string;
      required: boolean;
      doc: string;
    };
  };
  function_stop: {
    type: string;
    minimum: number;
    maximum: number;
    value: string[];
    length: number;
    doc: string;
  };
  expression: {
    type: string;
    value: string;
    minimum: number;
    doc: string;
  };
  expression_name: {
    doc: string;
    type: string;
    values: {
      let: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number | (string | number | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      var: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      literal: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      semiliteral: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[][])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      array: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string[];
            doc: string;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | (string | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      at: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number | (string | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      in: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "index-of": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      slice: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      case: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | (string | boolean | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      match: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string[];
            doc: string;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      coalesce: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | (string | string[])[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      step: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      interpolate: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string[];
          }[];
          parameters: ({
            name: string;
            type: string;
            doc: string;
          } | {
            name: string;
            type: string[];
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "interpolate-hcl": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string[];
          }[];
          parameters: ({
            name: string;
            type: string;
            doc: string;
          } | {
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string[];
            doc?: undefined;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      "interpolate-lab": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string[];
          }[];
          parameters: ({
            name: string;
            type: string;
            doc: string;
          } | {
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string[];
            doc?: undefined;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      ln2: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      pi: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      e: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      typeof: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      string: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      number: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      boolean: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | boolean | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      object: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      collator: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: {
              "case-sensitive": {
                type: string;
                default: boolean;
                example: boolean;
                doc: string;
              };
              "diacritic-sensitive": {
                type: string;
                default: boolean;
                example: boolean;
                doc: string;
              };
              locale: {
                type: string;
                example: string;
                doc: string;
              };
            };
          }[];
        };
        example: (string | {
          "case-sensitive": boolean;
          "diacritic-sensitive": boolean;
          locale: string;
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      format: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string[];
          } | {
            name: string;
            type: {
              "text-font": {
                type: string;
                doc: string;
                example: string;
              };
              "text-color": {
                type: string;
                doc: string;
                example: string;
              };
              "font-scale": {
                type: string;
                doc: string;
                example: number;
              };
              "vertical-align": {
                type: string;
                doc: string;
                default: string;
                example: string;
                values: {
                  bottom: {
                    doc: string;
                  };
                  center: {
                    doc: string;
                  };
                  top: {
                    doc: string;
                  };
                };
              };
            };
          })[];
        };
        example: (string | (string | string[])[] | {
          "font-scale": number;
          "vertical-align"?: undefined;
        } | {
          "font-scale"?: undefined;
          "vertical-align"?: undefined;
        } | {
          "font-scale": number;
          "vertical-align": string;
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          "text-font": {
            js: string;
            android: string;
            ios: string;
          };
          "font-scale": {
            js: string;
            android: string;
            ios: string;
          };
          "text-color": {
            js: string;
            android: string;
            ios: string;
          };
          "vertical-align": {
            js: string;
            android: string;
            ios: string;
          };
          image: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      image: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "global-state": {
        doc: string;
        group: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "number-format": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc: string;
          } | {
            name: string;
            type: {
              locale: {
                type: string;
                example: string;
                doc: string;
              };
              currency: {
                type: string;
                example: string;
                doc: string;
              };
              unit: {
                type: string;
                example: string;
                doc: string;
              };
              "min-fraction-digits": {
                type: string;
                example: number;
                doc: string;
              };
              "max-fraction-digits": {
                type: string;
                example: number;
                doc: string;
              };
            };
            doc: string;
          })[];
        };
        example: (string | string[] | {
          "min-fraction-digits": number;
          "max-fraction-digits": number;
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          "`unit` property": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-string": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-number": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-boolean": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-rgba": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "to-color": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      rgb: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      rgba: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      get: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      has: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      length: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string[];
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      properties: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "feature-state": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      "geometry-type": {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      id: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      zoom: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "heatmap-density": {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      elevation: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "line-progress": {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      accumulated: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      "+": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "*": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "-": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "/": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "%": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "^": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      sqrt: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      log10: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      ln: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      log2: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      sin: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      cos: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      tan: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      asin: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      acos: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      atan: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      min: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      max: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      round: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      abs: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      ceil: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      floor: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | number)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      distance: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | {
          type: string;
          coordinates: number[];
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "==": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "!=": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | boolean)[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      ">": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "<": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      ">=": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "<=": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: ({
            name: string;
            type: string;
            doc?: undefined;
          } | {
            name: string;
            type: string;
            doc: string;
          })[];
        };
        example: (string | number | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
          collator: {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      all: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | number | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      any: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | number | string[])[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "!": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      within: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | {
          type: string;
          coordinates: number[][][];
        })[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "is-supported-script": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: string[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      upcase: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      downcase: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      concat: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      "resolved-locale": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | {
          "case-sensitive": boolean;
          "diacritic-sensitive": boolean;
          locale: string;
        })[])[];
        group: string;
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      split: {
        doc: string;
        group: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | string[])[];
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
      join: {
        doc: string;
        group: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
          }[];
        };
        example: (string | (string | string[])[])[];
        "sdk-support": {
          "basic functionality": {
            js: string;
            android: string;
            ios: string;
          };
        };
      };
    };
  };
  light: {
    anchor: {
      type: string;
      default: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      "property-type": string;
      transition: boolean;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      doc: string;
      example: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    position: {
      type: string;
      default: number[];
      length: number;
      value: string;
      "property-type": string;
      transition: boolean;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      doc: string;
      example: number[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    color: {
      type: string;
      "property-type": string;
      default: string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    intensity: {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
  };
  sky: {
    "sky-color": {
      type: string;
      "property-type": string;
      default: string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "horizon-color": {
      type: string;
      "property-type": string;
      default: string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "fog-color": {
      type: string;
      "property-type": string;
      default: string;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "fog-ground-blend": {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "horizon-fog-blend": {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "sky-horizon-blend": {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
    "atmosphere-blend": {
      type: string;
      "property-type": string;
      default: number;
      minimum: number;
      maximum: number;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
    };
  };
  terrain: {
    source: {
      type: string;
      doc: string;
      required: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
    exaggeration: {
      type: string;
      minimum: number;
      doc: string;
      default: number;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
      };
    };
  };
  projection: {
    type: {
      type: string;
      doc: string;
      default: string;
      "property-type": string;
      transition: boolean;
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
    };
  };
  paint: string[];
  paint_fill: {
    "fill-antialias": {
      type: string;
      default: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-layer-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "SDF fill pattern colorization": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-outline-color": {
      type: string;
      doc: string;
      transition: boolean;
      requires: ({
        "!": string;
        "fill-antialias"?: undefined;
      } | {
        "fill-antialias": boolean;
        "!"?: undefined;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-pattern": {
      type: string;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  "paint_fill-extrusion": {
    "fill-extrusion-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      requires: {
        "!": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-pattern": {
      type: string;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-height": {
      type: string;
      default: number;
      units: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
        "negative values": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-base": {
      type: string;
      default: number;
      units: string;
      doc: string;
      transition: boolean;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
        "negative values": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "fill-extrusion-vertical-gradient": {
      type: string;
      default: boolean;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          ios: string;
          android: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_line: {
    "line-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-layer-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-color": {
      type: string;
      doc: string;
      default: string;
      transition: boolean;
      requires: {
        "!": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-width": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-gap-width": {
      type: string;
      default: number;
      minimum: number;
      doc: string;
      transition: boolean;
      units: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-offset": {
      type: string;
      default: number;
      doc: string;
      transition: boolean;
      units: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-blur": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-dasharray": {
      type: string;
      value: string;
      doc: string;
      minimum: number;
      transition: boolean;
      units: string;
      requires: {
        "!": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          ios: string;
          android: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-pattern": {
      type: string;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "line-gradient": {
      type: string;
      doc: string;
      transition: boolean;
      requires: ({
        "!": string;
        source?: undefined;
        has?: undefined;
      } | {
        source: string;
        has: {
          lineMetrics: boolean;
        };
        "!"?: undefined;
      })[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {};
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_circle: {
    "circle-radius": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-blur": {
      type: string;
      default: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-pitch-scale": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-pitch-alignment": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-stroke-width": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-stroke-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "circle-stroke-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_heatmap: {
    "heatmap-radius": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "heatmap-weight": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "heatmap-intensity": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "heatmap-color": {
      type: string;
      default: (string | number | string[])[];
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {};
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "heatmap-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_symbol: {
    "icon-opacity": {
      doc: string;
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-color": {
      type: string;
      default: string;
      transition: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-halo-color": {
      type: string;
      default: string;
      transition: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-halo-width": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-halo-blur": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "icon-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-color": {
      type: string;
      doc: string;
      default: string;
      transition: boolean;
      overridable: boolean;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-halo-color": {
      type: string;
      default: string;
      transition: boolean;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-halo-width": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-halo-blur": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-translate": {
      type: string;
      value: string;
      length: number;
      default: number[];
      transition: boolean;
      units: string;
      doc: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "text-translate-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      doc: string;
      default: string;
      requires: string[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_raster: {
    "raster-opacity": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-hue-rotate": {
      type: string;
      default: number;
      period: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-brightness-min": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-brightness-max": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-saturation": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-contrast": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    resampling: {
      type: string;
      doc: string;
      values: {
        linear: {
          doc: string;
        };
        nearest: {
          doc: string;
        };
      };
      default: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-resampling": {
      type: string;
      doc: string;
      values: {
        linear: {
          doc: string;
        };
        nearest: {
          doc: string;
        };
      };
      default: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "raster-fade-duration": {
      type: string;
      default: number;
      minimum: number;
      transition: boolean;
      units: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_hillshade: {
    "hillshade-illumination-direction": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        multidirectional: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-illumination-altitude": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        multidirectional: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-illumination-anchor": {
      type: string;
      values: {
        map: {
          doc: string;
        };
        viewport: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-exaggeration": {
      type: string;
      doc: string;
      default: number;
      minimum: number;
      maximum: number;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-shadow-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        multidirectional: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-highlight-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        multidirectional: {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-accent-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "hillshade-method": {
      type: string;
      values: {
        standard: {
          doc: string;
        };
        basic: {
          doc: string;
        };
        combined: {
          doc: string;
        };
        igor: {
          doc: string;
        };
        multidirectional: {
          doc: string;
        };
      };
      default: string;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    resampling: {
      type: string;
      doc: string;
      values: {
        linear: {
          doc: string;
        };
        nearest: {
          doc: string;
        };
      };
      default: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  "paint_color-relief": {
    "color-relief-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "color-relief-color": {
      type: string;
      doc: string;
      example: (string | number | string[])[];
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {};
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    resampling: {
      type: string;
      doc: string;
      values: {
        linear: {
          doc: string;
        };
        nearest: {
          doc: string;
        };
      };
      default: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  paint_background: {
    "background-color": {
      type: string;
      default: string;
      doc: string;
      transition: boolean;
      requires: {
        "!": string;
      }[];
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "background-pattern": {
      type: string;
      transition: boolean;
      doc: string;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "data-driven styling": {};
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
    "background-opacity": {
      type: string;
      default: number;
      minimum: number;
      maximum: number;
      doc: string;
      transition: boolean;
      "sdk-support": {
        "basic functionality": {
          js: string;
          android: string;
          ios: string;
        };
        "[`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression": {
          js: string;
          android: string;
          ios: string;
        };
      };
      expression: {
        interpolated: boolean;
        parameters: string[];
      };
      "property-type": string;
    };
  };
  transition: {
    duration: {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
    };
    delay: {
      type: string;
      default: number;
      minimum: number;
      units: string;
      doc: string;
    };
  };
  "property-type": {
    "data-driven": {
      type: string;
      doc: string;
    };
    "cross-faded": {
      type: string;
      doc: string;
    };
    "cross-faded-data-driven": {
      type: string;
      doc: string;
    };
    "color-ramp": {
      type: string;
      doc: string;
    };
    "data-constant": {
      type: string;
      doc: string;
    };
    constant: {
      type: string;
      doc: string;
    };
  };
  promoteId: {
    "*": {
      type: string;
      doc: string;
    };
  };
  interpolation: {
    type: string;
    value: string;
    minimum: number;
    doc: string;
  };
  interpolation_name: {
    doc: string;
    type: string;
    values: {
      linear: {
        doc: string;
        syntax: {
          overloads: {
            parameters: any[];
            "output-type": string;
          }[];
          parameters: any[];
        };
        example: string[];
        "sdk-support": {
          interpolate: {
            js: string;
            android: string;
            ios: string;
          };
          "interpolate-hcl": {
            js: string;
            ios: string;
            android: string;
          };
          "interpolate-lab": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      exponential: {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        "sdk-support": {
          interpolate: {
            js: string;
            android: string;
            ios: string;
          };
          "interpolate-hcl": {
            js: string;
            ios: string;
            android: string;
          };
          "interpolate-lab": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
      "cubic-bezier": {
        doc: string;
        syntax: {
          overloads: {
            parameters: string[];
            "output-type": string;
          }[];
          parameters: {
            name: string;
            type: string;
            doc: string;
          }[];
        };
        example: (string | number)[];
        "sdk-support": {
          interpolate: {
            js: string;
            android: string;
            ios: string;
          };
          "interpolate-hcl": {
            js: string;
            ios: string;
            android: string;
          };
          "interpolate-lab": {
            js: string;
            ios: string;
            android: string;
          };
        };
      };
    };
  };
}): Array<ValidationError>;
export declare namespace validateStyleMin {
  var source: (...args: any[]) => any[];
  var sprite: (...args: any[]) => any[];
  var glyphs: (...args: any[]) => any[];
  var fontFaces: (...args: any[]) => any[];
  var light: (...args: any[]) => any[];
  var sky: (...args: any[]) => any[];
  var terrain: (...args: any[]) => any[];
  var state: (...args: any[]) => any[];
  var layer: (...args: any[]) => any[];
  var filter: (...args: any[]) => any[];
  var paintProperty: (...args: any[]) => any[];
  var layoutProperty: (...args: any[]) => any[];
}
//#endregion
//#region src/expression/definitions/step.d.ts
export declare class Step implements Expression {
  type: Type;
  input: Expression;
  readonly key: string;
  labels: Array<number>;
  outputs: Array<Expression>;
  constructor(type: Type, input: Expression, stops: Stops, key: string);
  static parse(args: ReadonlyArray<unknown>, context: ParsingContext): Expression;
  evaluate(ctx: EvaluationContext): any;
  eachChild(fn: (_: Expression) => void): void;
  outputDefined(): boolean;
}
//#endregion
//#region src/expression/definitions/format.d.ts
type FormattedSectionExpression = {
  content: Expression;
  scale: Expression | null;
  font: Expression | null;
  textColor: Expression | null;
  verticalAlign: Expression | null;
};
export declare class FormatExpression implements Expression {
  type: Type;
  sections: Array<FormattedSectionExpression>;
  constructor(sections: Array<FormattedSectionExpression>);
  static parse(args: ReadonlyArray<unknown>, context: ParsingContext): Expression;
  evaluate(ctx: EvaluationContext): Formatted;
  eachChild(fn: (_: Expression) => void): void;
  outputDefined(): boolean;
}
//#endregion
//#region src/expression/definitions/literal.d.ts
export declare class Literal implements Expression {
  type: Type;
  value: Value;
  constructor(type: Type, value: Value);
  static parse(args: ReadonlyArray<unknown>, context: ParsingContext): Expression;
  evaluate(): Value;
  eachChild(): void;
  outputDefined(): boolean;
}
//#endregion
//#region src/expression/compound_expression.d.ts
type Varargs = {
  type: Type;
};
type Signature = Array<Type> | Varargs;
type Evaluate = (b: EvaluationContext, a: Array<Expression>, key: string) => Value;
type Definition = [Type, Signature, Evaluate] | {
  type: Type;
  overloads: Array<[Signature, Evaluate]>;
};
export declare class CompoundExpression implements Expression {
  name: string;
  type: Type;
  _evaluate: Evaluate;
  args: Array<Expression>;
  readonly key: string;
  static definitions: {
    [_: string]: Definition;
  };
  constructor(name: string, type: Type, evaluate: Evaluate, args: Array<Expression>, key: string);
  evaluate(ctx: EvaluationContext): Value;
  eachChild(fn: (_: Expression) => void): void;
  outputDefined(): boolean;
  static parse(args: ReadonlyArray<unknown>, context: ParsingContext): Expression;
  static register(registry: ExpressionRegistry, definitions: {
    [_: string]: Definition;
  }): void;
}
//#endregion
//#region src/format.d.ts
/**
 * Format a MapLibre Style.  Returns a stringified style with its keys
 * sorted in the same order as the reference style.
 *
 * The optional `space` argument is passed to
 * [`JSON.stringify`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify)
 * to generate formatted output.
 *
 * If `space` is unspecified, a default of `2` spaces will be used.
 *
 * @private
 * @param {Object} style a MapLibre Style
 * @param {number} [space] space argument to pass to `JSON.stringify`
 * @returns {string} stringified formatted JSON
 * @example
 * var fs = require('fs');
 * var format = require('maplibre-gl-style-spec').format;
 * var style = fs.readFileSync('./source.json', 'utf8');
 * fs.writeFileSync('./dest.json', format(style));
 * fs.writeFileSync('./dest.min.json', format(style, 0));
 */
export declare function format(style: any, space?: number): string;
//#endregion
//#region src/validate/validate.d.ts
/**
 * Main recursive validation function used internally.
 * You should use `validateStyleMin` in the browser or `validateStyle` in node env.
 * @param options - the options object
 * @param options.key - string representing location of validation in style tree. Used only
 * for more informative error reporting.
 * @param options.value - current value from style being evaluated. May be anything from a
 * high level object that needs to be descended into deeper or a simple
 * scalar value.
 * @param options.valueSpec - current spec being evaluated. Tracks value.
 * @param options.styleSpec - current full spec being evaluated.
 * @param options.validateSpec - the validate function itself
 * @param options.style - the style object
 * @param options.objectElementValidators - optional object of functions that will be called
 * @returns an array of errors, or an empty array if no errors are found.
 */
export declare function validate(options: {
  key: any;
  value: any;
  valueSpec: any;
  styleSpec: any;
  validateSpec?: any;
  style: any;
  objectElementValidators?: any;
}): ValidationError[];
//#endregion
//#region src/migrate.d.ts
/**
 * Migrate a Mapbox/MapLibre GL Style to the latest version.
 *
 * @param style - a MapLibre Style
 * @returns a migrated style
 * @example
 * const fs = require('fs');
 * const migrate = require('@maplibre/maplibre-gl-style-spec').migrate;
 * const style = fs.readFileSync('./style.json', 'utf8');
 * fs.writeFileSync('./style.json', JSON.stringify(migrate(style)));
 */
export declare function migrate(style: StyleSpecification): StyleSpecification;
//#endregion
//#region src/util/classify_rings.d.ts
type RingWithArea<T extends Point2D> = T[] & {
  area?: number;
};
/**
 * Classifies an array of rings into polygons with outer rings and holes
 * @param rings - the rings to classify
 * @param maxRings - the maximum number of rings to include in a polygon, use 0 to include all rings
 * @returns an array of polygons with internal rings as holes
 */
export declare function classifyRings<T extends Point2D>(rings: RingWithArea<T>[], maxRings?: number): RingWithArea<T>[][];
//#endregion
//#region src/expression/visibility.d.ts
interface VisibilityExpression {
  /**
   * Evaluates the visibility expression and returns either 'visible' or 'none'.
   */
  evaluate: () => 'visible' | 'none';
  /**
   * Updates the visibility specification.
   */
  setValue: (visibility: VisibilitySpecification) => void;
  /**
   * Returns the set of global state properties referenced by the expression.
   */
  getGlobalStateRefs: () => Set<string>;
}
/**
 * Creates a visibility expression from a visibility specification.
 * @param visibility - the visibility specification, literal or expression
 * @param rootKey - location of the visibility value in the style JSON
 * (e.g. `layers[3].layout.visibility`), used to prefix runtime warnings
 * @param globalState - the global state object
 * @returns visibility expression object
 */
declare function createVisibility(visibility: VisibilitySpecification, rootKey: string, globalState: Record<string, any>): VisibilityExpression;
//#endregion
//#region src/index.d.ts
type ExpressionType = 'data-driven' | 'cross-faded' | 'cross-faded-data-driven' | 'color-ramp' | 'data-constant' | 'constant';
type ExpressionParameters = Array<'zoom' | 'feature' | 'feature-state' | 'heatmap-density' | 'elevation' | 'line-progress' | 'global-state'>;
type ExpressionSpecificationDefinition = {
  interpolated: boolean;
  parameters: ExpressionParameters;
};
export type StylePropertySpecification = {
  type: 'number';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: number;
} | {
  type: 'string';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: string;
  tokens?: boolean;
} | {
  type: 'boolean';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: boolean;
} | {
  type: 'enum';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  values: {
    [_: string]: {};
  };
  transition: boolean;
  default?: string;
} | {
  type: 'color';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: ColorSpecification;
  overridable: boolean;
} | {
  type: 'array';
  value: 'number';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  length?: number;
  transition: boolean;
  default?: Array<number>;
} | {
  type: 'array';
  value: 'string';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  length?: number;
  transition: boolean;
  default?: Array<string>;
} | {
  type: 'padding';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: PaddingSpecification;
} | {
  type: 'numberArray';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: NumberArraySpecification;
} | {
  type: 'colorArray';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: ColorArraySpecification;
} | {
  type: 'variableAnchorOffsetCollection';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: VariableAnchorOffsetCollectionSpecification;
} | {
  type: 'projectionDefinition';
  'property-type': ExpressionType;
  expression?: ExpressionSpecificationDefinition;
  transition: boolean;
  default?: ProjectionDefinitionSpecification;
};
declare const expression: {
  StyleExpression: typeof StyleExpression;
  StylePropertyFunction: typeof StylePropertyFunction;
  ZoomConstantExpression: typeof ZoomConstantExpression;
  ZoomDependentExpression: typeof ZoomDependentExpression;
  createExpression: typeof createExpression;
  createPropertyExpression: typeof createPropertyExpression;
  isExpression: typeof isExpression;
  isExpressionFilter: typeof isExpressionFilter;
  isZoomExpression: typeof isZoomExpression;
  normalizePropertyExpression: typeof normalizePropertyExpression;
};
declare const styleFunction: {
  convertFunction: typeof convertFunction;
  createFunction: typeof createFunction;
  isFunction: typeof isFunction;
};
declare const visit: {
  eachLayer: typeof eachLayer;
  eachProperty: typeof eachProperty;
  eachSource: typeof eachSource;
};
//#endregion
export { type AllLayoutProperties, type AllPaintProperties, type BackgroundLayerSpecification, type CameraFunctionSpecification, type CircleLayerSpecification, type CollatorExpressionSpecification, type ColorArraySpecification, type ColorReliefLayerSpecification, type ColorSpecification, type CompositeExpression, type CompositeFunctionSpecification, type DataDrivenPropertyValueSpecification, type DiffCommand, type DiffOperations, type Expression, type ExpressionFilterSpecification, type ExpressionInputType, type ExpressionSpecification, type Feature, type FeatureFilter, type FeatureState, type FillExtrusionLayerSpecification, type FillLayerSpecification, type FilterSpecification, type FontFacesSpecification, type FormattedSpecification, type GeoJSONSourceSpecification, type GlobalProperties, type HeatmapLayerSpecification, type HillshadeLayerSpecification, type ICanonicalTileID, type ILngLat, type ILngLatLike, type IMercatorCoordinate, type ImageSourceSpecification, type InterpolationSpecification, type InterpolationType, type LayerSpecification, type LegacyFilterSpecification, type LightSpecification, type LineLayerSpecification, type MLFontFace, type NumberArraySpecification, type PaddingSpecification, type Point2D, type ProjectionDefinitionSpecification, type ProjectionDefinitionT, type ProjectionSpecification, type PromoteIdSpecification, type PropertyValueSpecification, type RasterDEMSourceSpecification, type RasterLayerSpecification, type RasterSourceSpecification, type ResolvedImageSpecification, type SchemaSpecification, type SkySpecification, type SourceExpression, type SourceFunctionSpecification, type SourceSpecification, type SpriteSpecification, type StateSpecification, type StylePropertyExpression, type StyleSpecification, type StyleSpecificationReference, type SymbolLayerSpecification, type TerrainSpecification, type TransitionSpecification, type Type, type ValidationSeverity, type VariableAnchorOffsetCollectionSpecification, type VariableExpressionSpecification, type VectorSourceSpecification, type VerticalAlign, type VideoSourceSpecification, type VisibilityExpression, type VisibilitySpecification, createVisibility as createVisibilityExpression, expression, styleFunction as function, interpolateFactory as interpolates, latest, latest as v8, typeToString as toString, visit };