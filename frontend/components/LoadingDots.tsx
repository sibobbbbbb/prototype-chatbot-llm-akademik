export default function LoadingDots() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-white rounded-2xl shadow-md border border-gray-100 px-5 py-4">
        <div className="flex gap-2">
          <div className="w-3 h-3 bg-violet-600 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
          <div className="w-3 h-3 bg-violet-600 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
          <div className="w-3 h-3 bg-violet-600 rounded-full animate-bounce"></div>
        </div>
      </div>
    </div>
  );
}
