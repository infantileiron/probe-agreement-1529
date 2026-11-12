<script setup lang="ts">defineProps<{message:string}>()</script><template><div v-if="message" class="notice" role="alert">{{message}} <span>请调整输入后重试。</span></div></template>
