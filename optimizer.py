import random
import math
from recommender import travel_time_minutes
from copy import deepcopy
import datetime

class ItineraryGA:
    def __init__(self, poi_list, user_profile, pop_size=40, generations=100, mutation_rate=0.12):
        """
        poi_list: list of POI dicts (with lat/lon and opening hours if available)
        user_profile: { start_time: "09:00", end_time: "18:00", days: 1, transport: 'walking' }
        """
        self.pois = poi_list
        self.user = user_profile
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate

    def random_chromosome(self):
        chrom = deepcopy(self.pois)
        random.shuffle(chrom)
        return chrom

    def initial_pop(self):
        return [self.random_chromosome() for _ in range(self.pop_size)]

    def fitness(self, chrom):
        # Objective: maximize sum of poi scores, penalize travel time > available
        total_score = 0.0
        total_travel = 0.0
        # sum poi 'score' if present else 1
        prev = None
        for p in chrom:
            total_score += p.get("score", 1.0)
            if prev is not None:
                t = travel_time_minutes(prev["lat"], prev["lon"], p["lat"], p["lon"], self.user.get("transport","walking"))
                total_travel += t
            prev = p
        # available minutes in day
        start = datetime.datetime.strptime(self.user.get("start_time","09:00"), "%H:%M")
        end = datetime.datetime.strptime(self.user.get("end_time","18:00"), "%H:%M")
        available = (end - start).seconds / 60.0
        # simple penalty
        penalty = 0.0
        if total_travel > available * 0.6:  # e.g., if travel too much
            penalty += (total_travel - available * 0.6) / available
        # combine: high score better, less travel better
        fitness_value = total_score - penalty * 5.0 - (total_travel / 60.0) * 0.1
        return fitness_value

    def select(self, population, fitnesses):
        # tournament selection
        selected = []
        for _ in range(len(population)):
            a,b = random.sample(range(len(population)), 2)
            winner = population[a] if fitnesses[a] > fitnesses[b] else population[b]
            selected.append(winner)
        return selected

    def crossover(self, parent1, parent2):
        # ordered crossover (OX)
        size = len(parent1)
        if size < 2:
            return deepcopy(parent1)
        a, b = sorted(random.sample(range(size), 2))
        child = [None]*size
        child[a:b] = parent1[a:b]
        fill_pos = b
        for g in parent2[b:] + parent2[:b]:
            if g not in child:
                if fill_pos >= size: fill_pos = 0
                child[fill_pos] = g
                fill_pos += 1
        # fix any None (edge-case)
        for i in range(size):
            if child[i] is None:
                for cand in parent1:
                    if cand not in child:
                        child[i] = cand
                        break
        return child

    def mutate(self, chrom):
        # swap mutation
        size = len(chrom)
        if random.random() < self.mutation_rate:
            i,j = random.sample(range(size),2)
            chrom[i], chrom[j] = chrom[j], chrom[i]

    def run(self):
        pop = self.initial_pop()
        best = None
        best_score = -1e9
        for gen in range(self.generations):
            fitnesses = [self.fitness(c) for c in pop]
            for i,fv in enumerate(fitnesses):
                if fv > best_score:
                    best_score = fv
                    best = deepcopy(pop[i])
            # selection
            selected = self.select(pop, fitnesses)
            # crossover to produce new pop
            new_pop = []
            for i in range(0, len(selected), 2):
                p1 = selected[i]
                p2 = selected[(i+1) % len(selected)]
                child1 = self.crossover(p1, p2)
                child2 = self.crossover(p2, p1)
                self.mutate(child1)
                self.mutate(child2)
                new_pop.extend([child1, child2])
            pop = new_pop[:self.pop_size]
        # After GA, build a simple day plan by time accounting
        itinerary = self.build_daily_plan(best)
        return itinerary

    def build_daily_plan(self, chrom):
        start = datetime.datetime.strptime(self.user.get("start_time","09:00"), "%H:%M")
        end = datetime.datetime.strptime(self.user.get("end_time","18:00"), "%H:%M")
        current_time = start
        plan = []
        prev = None
        for p in chrom:
            if prev:
                tt = travel_time_minutes(prev["lat"], prev["lon"], p["lat"], p["lon"], self.user.get("transport","walking"))
            else:
                tt = 0
            arrival = current_time + datetime.timedelta(minutes=tt)
            visit_duration = datetime.timedelta(minutes=60)
            finish = arrival + visit_duration
            if finish > end:
                break

            poi_copy = deepcopy(p)  # ✅ keep all original fields
            poi_copy.update({
                "arrival": arrival.strftime("%H:%M"),
                "departure": finish.strftime("%H:%M"),
            })
            plan.append({
                "xid": p["xid"],
                "name": p["name"],
                "lat": p["lat"],
                "lon": p["lon"],
                "arrival": arrival.strftime("%H:%M"),
                "departure": finish.strftime("%H:%M"),
                "score": p.get("score", 0)
            })

            current_time = finish
            prev = p
        return plan