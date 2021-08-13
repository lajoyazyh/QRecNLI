// /* global d3 $ */
import pipeService from '../../service/pipeService.js';
import DrawResult from './drawResult.js';
import VueVega from 'vue-vega';
import Vue from 'vue';

Vue.use(VueVega);

export default {
    name: 'ResultView',
    components: {},
    props: {},
    data() {
        return {
            containerId: 'resultContainer',
            nl: "",
            vlSpecs: [],
            explanation: "",
            count: 0,
        }
    },
    watch: {},
    mounted: function() {
        this.drawResult = new DrawResult(this.containerId);
        pipeService.onSQL(sql => {
            this.nl = sql["sql"];
        });
        pipeService.onSQLTrans(SQLTrans => {
            this.explanation = SQLTrans.text;
        });
        pipeService.onVLSpecs(vlSpecs => {
            this.vlSpecs = vlSpecs;
        })
    },
    methods: {
        load() {
            this.count += 2
        }
    }
}