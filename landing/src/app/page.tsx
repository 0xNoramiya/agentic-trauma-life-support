import Hero from "@/components/Hero";
import DoubleMeaning from "@/components/DoubleMeaning";
import WhyThisExists from "@/components/WhyThisExists";
import MemoryMath from "@/components/MemoryMath";
import Pipeline from "@/components/Pipeline";
import Benchmarks from "@/components/Benchmarks";
import DemoCases from "@/components/DemoCases";
import CredibilityMoment from "@/components/CredibilityMoment";
import ShipsWith from "@/components/ShipsWith";
import Closing from "@/components/Closing";

export default function Home() {
  return (
    <main>
      <Hero />
      <DoubleMeaning />
      <WhyThisExists />
      <MemoryMath />
      <Pipeline />
      <Benchmarks />
      <DemoCases />
      <CredibilityMoment />
      <ShipsWith />
      <Closing />
    </main>
  );
}
