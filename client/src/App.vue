<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { format, parseISO } from 'date-fns'
import { Pie, Line } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, CategoryScale, LinearScale, PointElement, LineElement } from 'chart.js'
import { Trash2, AlertCircle, X, MapPin, Clock, Calendar, CheckCircle2, ChevronLeft, ChevronRight } from 'lucide-vue-next'

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale, LinearScale, PointElement, LineElement)

const API_BASE = 'http://localhost:5000'

interface StatsData {
  total: number
  breakdown: {
    METAL: number
    PAPER: number
    PLASTIC: number
  }
}

interface HistoryRecord {
  _id: string
  waste_type: string
  confidence: number
  timestamp: string
  location: string
  image_path: string
}

const stats = ref<StatsData>({ total: 0, breakdown: { METAL: 0, PAPER: 0, PLASTIC: 0 } })
const history = ref<HistoryRecord[]>([])
const loading = ref(true)
const error = ref('')
const selectedRecord = ref<HistoryRecord | null>(null)
const currentPage = ref(1)
const itemsPerPage = 10

const paginatedHistory = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return history.value.slice(start, start + itemsPerPage)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(history.value.length / itemsPerPage))
})

let pollInterval: number

const pieChartData = ref({
  labels: ['Metal', 'Paper', 'Plastic'],
  datasets: [{
    data: [0, 0, 0],
    backgroundColor: ['#eab308', '#22c55e', '#3b82f6'],
    borderWidth: 0,
    hoverOffset: 4
  }]
})

const pieChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' as const }
  }
}

const lineChartData = ref({
  labels: [] as string[],
  datasets: [
    {
      label: 'Metal',
      data: [] as number[],
      borderColor: '#eab308',
      backgroundColor: 'rgba(234, 179, 8, 0.1)',
      borderWidth: 2,
      fill: true,
      tension: 0.4
    },
    {
      label: 'Paper',
      data: [] as number[],
      borderColor: '#22c55e',
      backgroundColor: 'rgba(34, 197, 94, 0.1)',
      borderWidth: 2,
      fill: true,
      tension: 0.4
    },
    {
      label: 'Plastic',
      data: [] as number[],
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      borderWidth: 2,
      fill: true,
      tension: 0.4
    }
  ]
})

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: true, position: 'bottom' as const } },
  scales: {
    y: { beginAtZero: true, ticks: { precision: 0 } }
  }
}

const fetchData = async () => {
  try {
    const [statsRes, historyRes] = await Promise.all([
      axios.get(`${API_BASE}/api/stats`),
      axios.get(`${API_BASE}/api/history?limit=100`)
    ])

    stats.value = statsRes.data
    history.value = historyRes.data.data

    // Update Pie Chart
    pieChartData.value.datasets[0].data = [
      stats.value.breakdown.METAL || 0,
      stats.value.breakdown.PAPER || 0,
      stats.value.breakdown.PLASTIC || 0
    ]

    // Update Line Chart (Group by day and waste type)
    const reversed = [...history.value].reverse()
    
    // Group by date string (e.g., "MMM dd")
    const grouped: Record<string, { METAL: number, PAPER: number, PLASTIC: number }> = {}
    reversed.forEach(item => {
      const dateStr = format(parseISO(item.timestamp), 'MMM dd')
      if (!grouped[dateStr]) grouped[dateStr] = { METAL: 0, PAPER: 0, PLASTIC: 0 }
      const type = item.waste_type.toUpperCase() as 'METAL' | 'PAPER' | 'PLASTIC'
      if (grouped[dateStr][type] !== undefined) {
        grouped[dateStr][type]++
      }
    })
    
    const labels = Object.keys(grouped)
    lineChartData.value = {
      labels: labels,
      datasets: [
        {
          ...lineChartData.value.datasets[0],
          data: labels.map(l => grouped[l].METAL)
        },
        {
          ...lineChartData.value.datasets[1],
          data: labels.map(l => grouped[l].PAPER)
        },
        {
          ...lineChartData.value.datasets[2],
          data: labels.map(l => grouped[l].PLASTIC)
        }
      ]
    }

    error.value = ''
  } catch (err: any) {
    console.error(err)
    error.value = 'Failed to fetch data from server. Ensure the backend is running.'
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  try {
    return format(parseISO(dateStr), 'MMM dd, yyyy HH:mm:ss')
  } catch {
    return dateStr
  }
}

const formatWasteType = (type: string) => {
  return type.charAt(0).toUpperCase() + type.slice(1).toLowerCase()
}

const getTypeColor = (type: string) => {
  switch (type.toUpperCase()) {
    case 'METAL': return 'text-yellow-600 bg-yellow-50'
    case 'PAPER': return 'text-green-600 bg-green-50'
    case 'PLASTIC': return 'text-blue-600 bg-blue-50'
    default: return 'text-gray-600 bg-gray-50'
  }
}

onMounted(() => {
  fetchData()
  // Poll every 5 seconds for real-time updates
  pollInterval = window.setInterval(fetchData, 5000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 font-sans p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-8">
      
      <!-- Header -->
      <header class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold tracking-tight text-gray-900 flex items-center gap-3">
            <Trash2 class="w-8 h-8 text-gray-700" />
            Waste Checker Dashboard
          </h1>
          <p class="text-gray-500 mt-1">Real-time IoT waste classification monitoring system.</p>
        </div>
        <div v-if="error" class="flex items-center gap-2 text-red-600 bg-red-50 px-4 py-2 rounded-lg text-sm shadow-soft">
          <AlertCircle class="w-4 h-4" />
          {{ error }}
        </div>
        <div v-else class="flex items-center gap-2 text-green-600 bg-green-50 px-4 py-2 rounded-lg text-sm shadow-soft">
          <span class="relative flex h-3 w-3">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          Live Sync Active
        </div>
      </header>

      <main v-if="loading && !history.length" class="flex justify-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </main>

      <main v-else class="space-y-8">
        
        <!-- Summary Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-white p-6 shadow-soft flex flex-col justify-between relative overflow-hidden">
            <h3 class="text-gray-500 text-sm font-medium">Total Items</h3>
            <p class="text-4xl font-bold mt-2">{{ stats.total }}</p>
            <div class="absolute -right-6 -bottom-6 opacity-5">
              <Trash2 class="w-32 h-32" />
            </div>
          </div>
          
          <div class="bg-white p-6 shadow-soft flex flex-col justify-between">
            <h3 class="text-yellow-600 text-sm font-medium">Metal</h3>
            <p class="text-3xl font-bold mt-2 text-gray-800">{{ stats.breakdown.METAL || 0 }}</p>
          </div>
          
          <div class="bg-white p-6 shadow-soft flex flex-col justify-between">
            <h3 class="text-green-600 text-sm font-medium">Paper</h3>
            <p class="text-3xl font-bold mt-2 text-gray-800">{{ stats.breakdown.PAPER || 0 }}</p>
          </div>
          
          <div class="bg-white p-6 shadow-soft flex flex-col justify-between">
            <h3 class="text-blue-600 text-sm font-medium">Plastic</h3>
            <p class="text-3xl font-bold mt-2 text-gray-800">{{ stats.breakdown.PLASTIC || 0 }}</p>
          </div>
        </div>

        <!-- Charts Row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="bg-white p-6 shadow-soft md:col-span-1">
            <h2 class="text-lg font-semibold mb-4 text-gray-800">Composition Ratio</h2>
            <div class="h-64 relative">
              <Pie v-if="stats.total > 0" :data="pieChartData" :options="pieChartOptions" />
              <div v-else class="absolute inset-0 flex items-center justify-center text-gray-400">No data</div>
            </div>
          </div>
          <div class="bg-white p-6 shadow-soft md:col-span-2">
            <h2 class="text-lg font-semibold mb-4 text-gray-800">Collection Trend (Daily)</h2>
            <div class="h-64 relative">
              <Line v-if="history.length > 0" :data="lineChartData" :options="lineChartOptions" />
              <div v-else class="absolute inset-0 flex items-center justify-center text-gray-400">No data</div>
            </div>
          </div>
        </div>

        <!-- History Table -->
        <div class="bg-white shadow-soft overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-white">
            <h2 class="text-lg font-semibold text-gray-800">Recent Classifications</h2>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-100">
              <thead class="bg-gray-50/50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-50">
                <tr v-for="record in paginatedHistory" :key="record._id" 
                    @click="selectedRecord = record"
                    class="hover:bg-gray-50 cursor-pointer transition-colors">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="['px-2.5 py-1 text-xs font-medium rounded-full', getTypeColor(record.waste_type)]">
                      {{ formatWasteType(record.waste_type) }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {{ record.confidence.toFixed(1) }}%
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(record.timestamp) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 truncate max-w-[200px]">
                    {{ record.location }}
                  </td>
                </tr>
                <tr v-if="history.length === 0">
                  <td colspan="4" class="px-6 py-12 text-center text-gray-500">
                    No records found in database.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination Controls -->
          <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50/50">
            <span class="text-sm text-gray-500">
              Showing <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span> to <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, history.length) }}</span> of <span class="font-medium">{{ history.length }}</span> results
            </span>
            <div class="flex items-center space-x-2">
              <button 
                @click="currentPage > 1 ? currentPage-- : null"
                :disabled="currentPage === 1"
                class="p-1 rounded-md border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft class="w-5 h-5" />
              </button>
              <span class="text-sm font-medium text-gray-700 mx-2">
                Page {{ currentPage }} of {{ totalPages }}
              </span>
              <button 
                @click="currentPage < totalPages ? currentPage++ : null"
                :disabled="currentPage === totalPages"
                class="p-1 rounded-md border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight class="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

      </main>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedRecord" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm transition-opacity" @click.self="selectedRecord = null">
      <div class="bg-white w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in duration-200">
        
        <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
          <h2 class="text-xl font-semibold text-gray-900 flex items-center gap-2">
            Classification Details
          </h2>
          <button @click="selectedRecord = null" class="text-gray-400 hover:text-gray-900 transition-colors">
            <X class="w-6 h-6" />
          </button>
        </div>
        
        <div class="p-6 overflow-y-auto custom-scrollbar flex-1 grid grid-cols-1 md:grid-cols-2 gap-8">
          
          <!-- Image Section -->
          <div class="space-y-4">
            <div class="aspect-square bg-gray-100 rounded-lg overflow-hidden border border-gray-100 relative group">
              <img 
                v-if="selectedRecord.image_path" 
                :src="`${API_BASE}/${selectedRecord.image_path}`" 
                alt="Waste Image" 
                class="w-full h-full object-cover"
                @error="(e) => (e.target as HTMLImageElement).src = 'data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'100%\' height=\'100%\' fill=\'%23f3f4f6\'><rect width=\'100%\' height=\'100%\'/></svg>'"
              />
              <div v-else class="flex h-full items-center justify-center text-gray-400">
                No Image
              </div>
            </div>
            
            <div class="bg-gray-50 p-4 rounded-lg">
              <div class="text-sm text-gray-500 mb-1">Detected Class</div>
              <div class="flex items-center justify-between">
                <span :class="['px-3 py-1 text-sm font-semibold rounded-full', getTypeColor(selectedRecord.waste_type)]">
                  {{ formatWasteType(selectedRecord.waste_type) }}
                </span>
                <span class="text-sm font-medium text-gray-700 bg-white px-2 py-1 rounded shadow-sm border border-gray-100">
                  {{ selectedRecord.confidence.toFixed(2) }}% confidence
                </span>
              </div>
            </div>
          </div>
          
          <!-- Info Section -->
          <div class="space-y-6">
            
            <div class="space-y-4">
              <div class="flex items-start gap-3">
                <Calendar class="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <div class="text-sm font-medium text-gray-900">Date & Time</div>
                  <div class="text-sm text-gray-500">{{ formatDate(selectedRecord.timestamp) }}</div>
                </div>
              </div>
              
              <div class="flex items-start gap-3">
                <MapPin class="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <div class="text-sm font-medium text-gray-900">Location</div>
                  <div class="text-sm text-gray-500">{{ selectedRecord.location || 'Unknown location' }}</div>
                </div>
              </div>
            </div>

            <!-- Embedded Map Placeholder based on extracted coords -->
            <div class="mt-4 border border-gray-100 rounded-lg overflow-hidden h-48 bg-gray-50 relative group">
              <!-- Using an iframe map from OpenStreetMap if coords exist -->
              <!-- The location string format is "City (Lat: X, Lon: Y)" or "Lat: X, Lon: Y" -->
              <iframe 
                v-if="selectedRecord.location.includes('Lat:')"
                width="100%" 
                height="100%" 
                frameborder="0" 
                scrolling="no" 
                marginheight="0" 
                marginwidth="0" 
                :src="`https://www.openstreetmap.org/export/embed.html?bbox=${parseFloat(selectedRecord.location.split('Lon:')[1]) - 0.005},${parseFloat(selectedRecord.location.match(/Lat: ([-\d.]+)/)?.[1] || 0) - 0.005},${parseFloat(selectedRecord.location.split('Lon:')[1]) + 0.005},${parseFloat(selectedRecord.location.match(/Lat: ([-\d.]+)/)?.[1] || 0) + 0.005}&layer=mapnik&marker=${parseFloat(selectedRecord.location.match(/Lat: ([-\d.]+)/)?.[1] || 0)},${parseFloat(selectedRecord.location.split('Lon:')[1])}`" 
                class="pointer-events-none group-hover:pointer-events-auto transition-all">
              </iframe>
              <div v-else class="flex h-full items-center justify-center text-gray-400 text-sm">
                Location map unavailable
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 10px;
}
</style>
